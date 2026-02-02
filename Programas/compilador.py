import sys
import os
import subprocess
import shutil
import json
import re
from datetime import datetime
import xml.etree.ElementTree as ET
from xml.etree.ElementTree import ParseError
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Lock
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QFileDialog, QVBoxLayout, QHBoxLayout, QFormLayout, QComboBox,
    QLabel, QPushButton, QLineEdit, QProgressBar, QTextEdit, QMenuBar, QMenu, QMessageBox, QCheckBox, QDialog, QDialogButtonBox
)
from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtGui import QFont, QAction

CONFIG_FILE = "compilador_config.json"

def normalizar_nombre_idioma(nombre: str) -> str:
    """
    Normaliza el nombre de la carpeta de idioma para usarlo como carpeta de salida.
    - Si el nombre contiene una parte entre paréntesis (normalmente al final), se elimina todo
      desde la primera ocurrencia de " (" en adelante. Ej: "Spanish (Español(Castellano))" -> "Spanish".
    - Si no existe el patrón " (", se intenta eliminar cualquier segmento final entre paréntesis,
      incluso con anidación, recortando desde el último "(" hasta el final mientras haya pares ().
    """
    if not isinstance(nombre, str):
        return ""
    nombre = nombre.strip()
    # Caso típico: idioma seguido de paréntesis con nombre nativo
    corte = nombre.find(" (")
    if corte != -1:
        return nombre[:corte].strip()
    # Fallback: eliminar segmentos entre paréntesis al final (maneja anidación simple)
    s = nombre
    while True:
        open_idx = s.rfind("(")
        close_idx = s.rfind(")")
        if open_idx != -1 and close_idx != -1 and close_idx > open_idx:
            s = s[:open_idx].rstrip()
        else:
            break
    return s.strip()

def indent_xml(elem, level=0, space="  "):
    """
    Función para indentar un árbol de ElementTree para una mejor legibilidad (pretty-printing).
    Modifica el árbol XML en su lugar.
    """
    i = "\n" + level * space
    if len(elem):
        if not elem.text or not elem.text.strip():
            elem.text = i + space
        if not elem.tail or not elem.tail.strip():
            elem.tail = i
        for subelem in elem:
            indent_xml(subelem, level + 1, space)
        if not subelem.tail or not subelem.tail.strip():
            subelem.tail = i
    else:
        if level and (not elem.tail or not elem.tail.strip()):
            elem.tail = i

class CopiadorThread(QThread):
    progreso = Signal(int)
    log = Signal(str)
    error_log = Signal(str)
    terminado = Signal(int)
    mods_count = Signal(int, int)  # mods_procesados, total_mods
    archivos_count = Signal(int)  # archivos_copiados

    def __init__(self, origen, destino, nombre_subcarpeta, limpiar_destino=False, eliminar_comentarios=False, parent=None):
        super().__init__(parent)
        self.origen = origen
        self.destino = destino
        self.limpiar_destino = limpiar_destino
        self.eliminar_comentarios = eliminar_comentarios
        self.nombre_subcarpeta = nombre_subcarpeta
        # Ajuste de carpeta de salida: quitar paréntesis y contenido
        # Ejemplo: 
        # "Spanish (Español(Castellano))" -> "Spanish"
        # "Russian (Русский)" -> "Russian"
        self.nombre_destino = normalizar_nombre_idioma(nombre_subcarpeta)
        self.archivos_copiados = 0
        self.mods_procesados = []
        # Lock para sincronizar acceso a variables compartidas en threads
        self._lock = Lock()
        self._mods_procesados_count = 0

    def run(self):
        try:
            # Limpiar carpeta de destino si se solicita
            ruta_destino_subcarpeta = os.path.join(self.destino, self.nombre_destino)
            if self.limpiar_destino and os.path.isdir(ruta_destino_subcarpeta):
                try:
                    self.log.emit(f"Limpiando carpeta de destino: {ruta_destino_subcarpeta}...")
                    shutil.rmtree(ruta_destino_subcarpeta)
                    self.log.emit("Carpeta de destino limpiada exitosamente.")
                except Exception as e:
                    msg = f"Error al limpiar la carpeta de destino: {str(e)}"
                    self.log.emit(msg)
                    self.error_log.emit(msg)
                    self.terminado.emit(0) # Abortar si la limpieza falla
                    return

            self.log.emit("Iniciando proceso de copia...")
            if self.eliminar_comentarios:
                self.log.emit("Opción 'Eliminar comentarios XML' está activada.")

            # Obtener lista de mods a procesar
            mods_a_procesar = [d for d in os.listdir(self.origen) if os.path.isdir(os.path.join(self.origen, d, self.nombre_subcarpeta))]
            self.mods_procesados = mods_a_procesar

            if not mods_a_procesar:
                self.log.emit("No se encontraron mods con traducciones para procesar.")
                self.terminado.emit(0)
                return

            total_mods = len(mods_a_procesar)
            self.log.emit(f"Se encontraron {total_mods} mods para procesar.")
            self.log.emit(f"Procesamiento paralelo: usando hasta 4 threads simultáneos para mayor velocidad.")
            self._mods_procesados_count = 0

            # Procesar mods en paralelo usando ThreadPoolExecutor
            with ThreadPoolExecutor(max_workers=4) as executor:
                # Enviar todos los mods para procesamiento paralelo
                futures = {executor.submit(self._procesar_mod, mod, total_mods): mod 
                          for mod in mods_a_procesar}
                
                # Ir obteniendo resultados conforme terminan
                for future in as_completed(futures):
                    mod_name = futures[future]
                    try:
                        future.result()  # Esto lanzará excepción si el mod falló
                    except Exception as e:
                        # Log de error ya fue emitido en _procesar_mod, solo continuar
                        pass

            self.log.emit(f"Proceso completado. Total de archivos copiados: {self.archivos_copiados}")
            self.terminado.emit(self.archivos_copiados)
        except Exception as e:
            # Capturar un error inesperado y registrar más detalles para depuración.
            import traceback
            tb_str = traceback.format_exc()
            msg = f"Ocurrió un error inesperado: {str(e)}"
            self.log.emit(msg)
            self.error_log.emit(f"{msg}\nDetalles:\n{tb_str}")
            self.terminado.emit(self.archivos_copiados)

    def _procesar_mod(self, mod, total_mods):
        """Procesa un mod individual. Este método se ejecuta en paralelo por ThreadPoolExecutor."""
        try:
            ruta_mod = os.path.join(self.origen, mod)
            ruta_idioma = os.path.join(ruta_mod, self.nombre_subcarpeta)

            # Contar archivos para el mod actual
            archivos_del_mod = []
            for carpeta_raiz, _, archivos in os.walk(ruta_idioma):
                for archivo in archivos:
                    if archivo.endswith(".xml"):
                        archivos_del_mod.append((carpeta_raiz, archivo))
            
            total_archivos_mod = len(archivos_del_mod)
            if total_archivos_mod == 0:
                self.log.emit(f"Sin archivos XML en {mod}, saltando.")
                with self._lock:
                    self._mods_procesados_count += 1
                    progreso_general = int((self._mods_procesados_count / total_mods) * 100)
                self.progreso.emit(progreso_general)
                return

            archivos_procesados_local = 0

            for carpeta_raiz, archivo in archivos_del_mod:
                ruta_origen = os.path.join(carpeta_raiz, archivo)
                ruta_relativa = os.path.relpath(carpeta_raiz, ruta_idioma)
                ruta_destino_base = os.path.join(self.destino, self.nombre_destino)
                ruta_destino_carpeta = os.path.join(ruta_destino_base, ruta_relativa)
                os.makedirs(ruta_destino_carpeta, exist_ok=True)
                nuevo_nombre = f"[{mod}]_{os.path.splitext(archivo)[0]}.xml"
                ruta_destino_archivo = os.path.join(ruta_destino_carpeta, nuevo_nombre)
                
                if self.eliminar_comentarios:
                    try:
                        # Usar un parser que ignora comentarios
                        parser = ET.XMLParser(target=ET.TreeBuilder(insert_comments=False))

                        # Leemos el contenido completo para limpiar caracteres invisibles
                        with open(ruta_origen, 'rb') as f:
                            raw_data = f.read()

                        # Intentamos decodificar (utf-8-sig maneja el BOM de VS Code automáticamente)
                        try:
                            content = raw_data.decode('utf-8-sig')
                        except UnicodeDecodeError:
                            # Fallback para archivos que realmente estén en UTF-16
                            content = raw_data.decode('utf-16')

                        # Limpieza crítica: eliminamos espacios, saltos de línea o nulos al inicio/final
                        content = content.strip()

                        # Si el XML tiene una declaración de encoding (ej: encoding="utf-16"), 
                        # al procesarlo como string de Python puede dar error. La removemos.
                        if content.startswith("<?xml"):
                            # Buscamos el final de la etiqueta de declaración ?>
                            content = content.split("?>", 1)[-1].strip()

                        # Escapar etiquetas de formato de RimWorld (color, size, b, i) para evitar errores
                        # Esto convierte <color...> en &lt;color...&gt; para que sea XML válido
                        # Usamos un patrón más robusto que maneja atributos con espacios y comillas
                        content = re.sub(r'<(/?(?:color|size|b|i)(?:\s+[^>]*?)?)>', r'&lt;\1&gt;', content, flags=re.IGNORECASE)

                        # Parseamos desde el string limpio
                        root = ET.fromstring(content, parser=parser)
                        
                        tree = ET.ElementTree(root)
                        
                        # Ordenar los elementos hijos de la raíz (LanguageData) alfabéticamente por su tag
                        root[:] = sorted(root, key=lambda child: child.tag)
                        # Re-indentar el árbol para un formato limpio y legible
                        indent_xml(root)
                        # Escribir el XML procesado en el archivo de destino
                        tree.write(ruta_destino_archivo, encoding='utf-8', xml_declaration=True)
                    except ParseError as e_parse:
                        msg = f"Error de formato XML en '{ruta_origen}', no se pudo procesar. Copiando tal cual. Error: {e_parse}"
                        self.log.emit(msg)
                        self.error_log.emit(msg)
                        # Si falla el parseo, es más seguro copiar el archivo original
                        shutil.copy2(ruta_origen, ruta_destino_archivo)
                    except Exception as e_process:
                        msg = f"Error procesando '{ruta_origen}': {e_process}"
                        self.log.emit(msg)
                        self.error_log.emit(msg)
                else:
                    shutil.copy2(ruta_origen, ruta_destino_archivo)
                
                # Incrementar contadores de forma thread-safe
                with self._lock:
                    self.archivos_copiados += 1
                    archivos_actual = self.archivos_copiados
                archivos_procesados_local += 1
                # Emitir señal para actualizar contador en UI
                self.archivos_count.emit(archivos_actual)

            # Actualizar progreso de forma thread-safe
            with self._lock:
                self._mods_procesados_count += 1
                progreso_general = int((self._mods_procesados_count / total_mods) * 100)
                count_actual = self._mods_procesados_count
            
            self.log.emit(f"--- Mod procesado '{mod}' ---")
            self.progreso.emit(progreso_general)
            self.mods_count.emit(count_actual, total_mods)
            
        except Exception as e:
            # Error específico del mod, registrar pero no detener otros threads
            import traceback
            msg = f"Error procesando mod '{mod}': {str(e)}"
            self.log.emit(msg)
            self.error_log.emit(f"{msg}\n{traceback.format_exc()}")
            # Actualizar contador incluso si falló
            with self._lock:
                self._mods_procesados_count += 1
                progreso_general = int((self._mods_procesados_count / total_mods) * 100)
            self.progreso.emit(progreso_general)

class CompresorThread(QThread):
    log = Signal(str)
    terminado = Signal(bool, str) # exito, ruta_o_mensaje_error
    error_log = Signal(str)

    def __init__(self, ruta_base, carpeta_a_comprimir, parent=None):
        super().__init__(parent)
        self.ruta_base = ruta_base
        self.carpeta_a_comprimir = carpeta_a_comprimir

    def run(self):
        try:
            ruta_carpeta_origen = os.path.join(self.ruta_base, self.carpeta_a_comprimir)
            if not os.path.isdir(ruta_carpeta_origen):
                msg = f"La carpeta a comprimir no existe: {ruta_carpeta_origen}"
                self.log.emit(msg)
                self.error_log.emit(msg)
                self.terminado.emit(False, msg)
                return

            nombre_archivo_salida = os.path.join(self.ruta_base, self.carpeta_a_comprimir)
            self.log.emit(f"Iniciando compresión de '{self.carpeta_a_comprimir}'...")
            
            archivo_comprimido = shutil.make_archive(
                base_name=nombre_archivo_salida,
                format='tar',
                root_dir=self.ruta_base,
                base_dir=self.carpeta_a_comprimir
            )
            self.log.emit(f"Compresión completada. Archivo creado: {archivo_comprimido}")

            # Eliminar la carpeta original después de comprimir
            try:
                self.log.emit(f"Eliminando la carpeta original: {ruta_carpeta_origen}...")
                shutil.rmtree(ruta_carpeta_origen)
                self.log.emit("Carpeta original eliminada exitosamente.")
            except Exception as e_clean:
                msg = f"ADVERTENCIA: No se pudo eliminar la carpeta original. Error: {str(e_clean)}"
                self.log.emit(msg)
                self.error_log.emit(msg)

            self.terminado.emit(True, archivo_comprimido)
        except Exception as e:
            error_msg = f"Error durante el proceso de compresión: {str(e)}"
            self.log.emit(error_msg)
            self.error_log.emit(error_msg)
            self.terminado.emit(False, error_msg)

class DialogoPersonalizarReporte(QDialog):
    def __init__(self, config, sample_mods, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Personalizar Reporte")
        self.setMinimumSize(810, 500)
        self.config = config.copy()
        self.sample_mods = sample_mods

        # Layout principal horizontal
        main_layout = QHBoxLayout(self)

        # --- Panel Izquierdo: Configuración ---
        config_widget = QWidget()
        config_v_layout = QVBoxLayout(config_widget)

        form_layout = QFormLayout()

        self.txt_titulo = QLineEdit(self.config.get("titulo", "Reporte de Mods Procesados"))
        self.chk_incluir_conteo = QCheckBox("Incluir conteo total de mods")
        self.chk_incluir_conteo.setChecked(self.config.get("incluir_conteo", True))
        self.chk_incluir_lista_mods = QCheckBox("Incluir lista de nombres de mods")
        self.chk_incluir_lista_mods.setChecked(self.config.get("incluir_lista_mods", True))
        self.txt_texto_adicional = QTextEdit(self.config.get("texto_adicional", ""))
        self.txt_texto_adicional.setPlaceholderText("Añade un encabezado o pie de página personalizado aquí...")
        self.txt_texto_adicional.setMaximumHeight(100)

        form_layout.addRow("Título del Reporte:", self.txt_titulo)
        form_layout.addRow(self.chk_incluir_conteo)
        form_layout.addRow(self.chk_incluir_lista_mods)
        form_layout.addRow("Texto Adicional:", self.txt_texto_adicional)

        self.chk_ruta_personalizada = QCheckBox("Usar ruta de reporte personalizada")
        self.chk_ruta_personalizada.setChecked(self.config.get("reporte_ruta_personalizada_enabled", False))

        self.widget_ruta_personalizada = QWidget()
        h_layout_ruta = QHBoxLayout(self.widget_ruta_personalizada)
        h_layout_ruta.setContentsMargins(0, 0, 0, 0)
        self.txt_ruta_reporte = QLineEdit(self.config.get("reporte_ruta_personalizada", ""))
        self.btn_seleccionar_ruta = QPushButton("Seleccionar")
        h_layout_ruta.addWidget(self.txt_ruta_reporte)
        h_layout_ruta.addWidget(self.btn_seleccionar_ruta)
        self.widget_ruta_personalizada.setEnabled(self.chk_ruta_personalizada.isChecked())

        self.chk_ruta_personalizada.toggled.connect(self.widget_ruta_personalizada.setEnabled)
        self.btn_seleccionar_ruta.clicked.connect(self.seleccionar_ruta_reporte)

        form_layout.addRow(self.chk_ruta_personalizada)
        form_layout.addRow("Ruta de Reporte:", self.widget_ruta_personalizada)

        config_v_layout.addLayout(form_layout)
        config_v_layout.addStretch()

        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        config_v_layout.addWidget(button_box)

        main_layout.addWidget(config_widget)

        # --- Panel Derecho: Vista Previa ---
        preview_widget = QWidget()
        preview_layout = QVBoxLayout(preview_widget)
        preview_label = QLabel("Vista Previa del Reporte:")
        self.preview_text = QTextEdit()
        self.preview_text.setReadOnly(True)
        self.preview_text.setFont(QFont("Courier New", 9))
        preview_layout.addWidget(preview_label)
        preview_layout.addWidget(self.preview_text)

        main_layout.addWidget(preview_widget, 1) # Stretch factor

        # --- Conexiones para la vista previa en vivo ---
        self.txt_titulo.textChanged.connect(self.actualizar_preview)
        self.chk_incluir_conteo.toggled.connect(self.actualizar_preview)
        self.chk_incluir_lista_mods.toggled.connect(self.actualizar_preview)
        self.txt_texto_adicional.textChanged.connect(self.actualizar_preview)

        self.actualizar_preview()

    def actualizar_preview(self):
        titulo = self.txt_titulo.text()
        incluir_conteo = self.chk_incluir_conteo.isChecked()
        incluir_lista = self.chk_incluir_lista_mods.isChecked()
        texto_adicional = self.txt_texto_adicional.toPlainText()

        preview_content = []
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        preview_content.append(f"{titulo} - {timestamp}")
        preview_content.append("=" * 50)
        if texto_adicional:
            preview_content.append(f"\n{texto_adicional}\n")
        if incluir_conteo:
            preview_content.append(f"Total de mods encontrados: {len(self.sample_mods)}\n")
        if incluir_lista:
            if self.sample_mods:
                preview_content.append("Lista de mods:")
                for mod in sorted(self.sample_mods):
                    preview_content.append(f"- {mod}")
            else:
                preview_content.append("Lista de mods:\n(No hay mods procesados para mostrar en la vista previa)")
        
        self.preview_text.setText("\n".join(preview_content))

    def seleccionar_ruta_reporte(self):
        carpeta = QFileDialog.getExistingDirectory(self, "Selecciona carpeta para los reportes", self.txt_ruta_reporte.text())
        if carpeta:
            self.txt_ruta_reporte.setText(carpeta)

    def get_config(self):
        self.config["titulo"] = self.txt_titulo.text()
        self.config["incluir_conteo"] = self.chk_incluir_conteo.isChecked()
        self.config["incluir_lista_mods"] = self.chk_incluir_lista_mods.isChecked()
        self.config["texto_adicional"] = self.txt_texto_adicional.toPlainText()
        self.config["reporte_ruta_personalizada_enabled"] = self.chk_ruta_personalizada.isChecked()
        self.config["reporte_ruta_personalizada"] = self.txt_ruta_reporte.text()
        return self.config

class VentanaPrincipal(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Compilador de Traducciones")
        self.setGeometry(100, 100, 700, 450)
        self.font_normal = QFont("Segoe UI", 10)
        self.font_titulo = QFont("Segoe UI", 14, QFont.Weight.Bold)
        self.origen = ""
        self.destino = ""
        self.idioma_seleccionado = ""
        self.compresor_hilo = None
        self.mods_procesados_en_ultimo_run = []
        self.opciones_default = {}
        self.reporte_config = {}
        self.hilo = None
        self.cargar_configuracion()
        self.init_ui()
        self.post_init_setup()

    def closeEvent(self, event):
        """Sobrescribe el evento de cierre para guardar la configuración."""
        self.guardar_configuracion()
        self.logear("Configuración guardada al salir de la aplicación.")
        event.accept()

    def init_ui(self):
        central = QWidget()
        main_layout = QVBoxLayout()

        h_origen = QHBoxLayout()
        lbl_origen = QLabel("Carpeta de origen:")
        self.txt_origen = QLineEdit(self.origen)
        btn_origen = QPushButton("Seleccionar")
        btn_origen.clicked.connect(self.seleccionar_origen)
        h_origen.addWidget(lbl_origen)
        h_origen.addWidget(self.txt_origen)
        h_origen.addWidget(btn_origen)
        main_layout.addLayout(h_origen)
        h_destino = QHBoxLayout()
        lbl_destino = QLabel("Carpeta de destino:")
        self.txt_destino = QLineEdit(self.destino)
        btn_destino = QPushButton("Seleccionar")
        btn_destino.clicked.connect(self.seleccionar_destino)
        h_destino.addWidget(lbl_destino)
        h_destino.addWidget(self.txt_destino)
        h_destino.addWidget(btn_destino)
        main_layout.addLayout(h_destino)
        h_idioma = QHBoxLayout()
        lbl_idioma = QLabel("Idioma a procesar:")
        self.cmb_idioma = QComboBox()
        self.cmb_idioma.setEditable(True)
        self.cmb_idioma.setPlaceholderText("Detecta o escribe el nombre de la carpeta de idioma...")
        self.cmb_idioma.setEnabled(False)
        btn_detectar = QPushButton("Detectar Idiomas")
        btn_detectar.clicked.connect(self.detectar_idiomas)
        h_idioma.addWidget(lbl_idioma)
        h_idioma.addWidget(self.cmb_idioma, 1)
        h_idioma.addWidget(btn_detectar)
        main_layout.addLayout(h_idioma)
        opciones_layout = QVBoxLayout()
        self.chk_limpiar_destino = QCheckBox("Limpiar carpeta de destino antes de procesar")
        self.chk_limpiar_destino.setToolTip(
            "Si se marca, eliminará la carpeta de idioma de destino y todo su contenido\n"
            "antes de iniciar la copia. Útil para una compilación limpia."
        )
        self.chk_eliminar_comentarios = QCheckBox("Eliminar comentarios de los archivos XML durante la copia")
        self.chk_eliminar_comentarios.setToolTip(
            "Si se marca, procesará los archivos XML para quitar comentarios y ordenará las etiquetas\n"
            "alfabéticamente. Puede ayudar a reducir el tamaño del archivo y mejorar la legibilidad."
        )
        self.chk_comprimir = QCheckBox("Comprimir resultado en un archivo .tar al finalizar")
        self.chk_comprimir.setToolTip(
            "Si se marca, después de copiar todos los archivos, creará un archivo .tar con la\n"
            "carpeta de idioma resultante y luego eliminará la carpeta original."
        )
        self.chk_update_about = QCheckBox("Actualizar About.xml (forceLoadAfter)")
        self.chk_update_about.setToolTip(
            "Si se marca, buscará ../About/about.xml relativo al destino y actualizará\n"
            "la lista <forceLoadAfter> con los IDs de los mods procesados."
        )
        opciones_layout.addWidget(self.chk_limpiar_destino)
        opciones_layout.addWidget(self.chk_eliminar_comentarios)
        opciones_layout.addWidget(self.chk_comprimir)
        opciones_layout.addWidget(self.chk_update_about)
        main_layout.addLayout(opciones_layout)
        h_accion = QHBoxLayout()
        self.lbl_contador_mods = QLabel("Mods procesados: 0")
        self.lbl_contador = QLabel("Archivos copiados: 0")
        self.btn_reporte = QPushButton("Generar informe")
        self.btn_reporte.setEnabled(False)
        self.btn_reporte.clicked.connect(self.generar_reporte)
        self.btn_procesar = QPushButton("Procesar")
        self.btn_procesar.clicked.connect(self.iniciar_proceso)
        h_accion.addWidget(self.lbl_contador_mods)
        h_accion.addWidget(self.lbl_contador)
        h_accion.addStretch()
        h_accion.addWidget(self.btn_reporte)
        h_accion.addWidget(self.btn_procesar)
        main_layout.addLayout(h_accion)
        self.progress = QProgressBar()
        self.progress.setValue(0)
        main_layout.addWidget(self.progress)
        lbl_registro = QLabel("Registro de actividad:")
        self.txt_log = QTextEdit()
        self.txt_log.setReadOnly(True)
        main_layout.addWidget(lbl_registro)
        main_layout.addWidget(self.txt_log)
        self.errores_widget = QWidget()
        log_errores_layout = QVBoxLayout(self.errores_widget)
        log_errores_layout.setContentsMargins(0, 10, 0, 0)
        lbl_errores = QLabel("Registro de errores:")
        self.txt_log_errores = QTextEdit()
        self.txt_log_errores.setReadOnly(True)
        # Limitar la altura para que no ocupe toda la ventana
        self.txt_log_errores.setMaximumHeight(150)
        log_errores_layout.addWidget(lbl_errores)
        log_errores_layout.addWidget(self.txt_log_errores)
        main_layout.addWidget(self.errores_widget)
        self.errores_widget.hide()
        central.setLayout(main_layout)
        self.setCentralWidget(central)
        self.crear_menu()

    def post_init_setup(self):
        if self.origen and os.path.isdir(self.origen):
            self.detectar_idiomas()

    def crear_menu(self):
        menubar = self.menuBar()
        archivo = menubar.addMenu("Archivo")

        config_menu = menubar.addMenu("Configuración")

        personalizar_reporte = QAction("Personalizar reporte", self)
        personalizar_reporte.triggered.connect(self.abrir_dialogo_personalizar_reporte)
        config_menu.addAction(personalizar_reporte)

        guardar_opciones = QAction("Guardar configuración actual", self)
        guardar_opciones.triggered.connect(self.guardar_estado_opciones)
        config_menu.addAction(guardar_opciones)

        config_menu.addSeparator()

        abrir_config = QAction("Abrir archivo de configuración", self)
        abrir_config.triggered.connect(self.abrir_archivo_config)
        config_menu.addAction(abrir_config)

        reset_rutas = QAction("Borrar rutas guardadas", self)
        reset_rutas.triggered.connect(self.restablecer_rutas)
        config_menu.addAction(reset_rutas)

        como_usar = menubar.addMenu("Cómo usar")
        ayuda_uso = QAction("Ver instrucciones", self)
        ayuda_uso.triggered.connect(self.mostrar_como_usar)
        como_usar.addAction(ayuda_uso)

        salir = QAction("Salir", self)
        salir.triggered.connect(self.close)
        archivo.addAction(salir)

        ayuda = menubar.addMenu("Ayuda")
        acerca = QAction("Acerca de", self)
        acerca.triggered.connect(self.mostrar_acerca_de)
        ayuda.addAction(acerca)

    def abrir_dialogo_personalizar_reporte(self):
        # Prepara datos de ejemplo para la vista previa
        sample_mods = []
        if self.mods_procesados_en_ultimo_run:
            sample_mods = self.mods_procesados_en_ultimo_run
        else:
            # Intentar obtener nombres de mods desde la carpeta de origen si no se ha ejecutado el proceso
            origen = self.txt_origen.text()
            if origen and os.path.isdir(origen):
                try:
                    # Obtener subdirectorios, que son los nombres de los mods
                    sample_mods = [d for d in os.listdir(origen) if os.path.isdir(os.path.join(origen, d))]
                except Exception:
                    sample_mods = [] # En caso de error, la lista estará vacía
            
            # Si no se encontraron mods en origen o no hay ruta, usar un ejemplo genérico
            if not sample_mods:
                sample_mods = ["ModDeEjemplo_A", "ModDeEjemplo_B", "ModDeEjemplo_Core"]

        dialogo = DialogoPersonalizarReporte(self.reporte_config, sample_mods, self)
        if dialogo.exec():
            self.reporte_config.update(dialogo.get_config())
            self.guardar_configuracion()
            self.logear("Configuración del reporte guardada.")

    def guardar_estado_opciones(self):
        reply = QMessageBox.question(self, 'Guardar Opciones',
                                     "¿Desea guardar el estado actual de las casillas de verificación (Limpiar, Eliminar comentarios, Comprimir) como predeterminado para futuros usos?",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            if not hasattr(self, 'opciones_default'):
                self.opciones_default = {}

            self.opciones_default['limpiar_destino'] = self.chk_limpiar_destino.isChecked()
            self.opciones_default['eliminar_comentarios'] = self.chk_eliminar_comentarios.isChecked()
            self.opciones_default['comprimir'] = self.chk_comprimir.isChecked()
            self.opciones_default['update_about'] = self.chk_update_about.isChecked()

            self.guardar_configuracion()
            self.logear("Estado de las opciones guardado como predeterminado.")
            QMessageBox.information(self, "Opciones Guardadas", "El estado actual de las opciones se ha guardado como predeterminado.")

    def abrir_archivo_config(self):
        config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), CONFIG_FILE)
        try:
            if not os.path.exists(config_path):
                self.guardar_configuracion()
                self.logear(f"Archivo de configuración no encontrado, se ha creado uno nuevo en: {config_path}")

            self.logear(f"Abriendo archivo de configuración: {config_path}")
            if sys.platform == "win32":
                os.startfile(config_path)
            elif sys.platform == "darwin":
                subprocess.Popen(["open", config_path])
            else:
                subprocess.Popen(["xdg-open", config_path])
        except Exception as e:
            error_msg = f"No se pudo abrir el archivo de configuración: {e}"
            self.logear_error(error_msg)
            QMessageBox.critical(self, "Error", error_msg)

    def restablecer_rutas(self):
        reply = QMessageBox.question(self, 'Confirmar Restablecimiento',
                                     "¿Está seguro de que desea borrar las rutas de origen y destino guardadas?",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            self.txt_origen.setText("")
            self.txt_destino.setText("")
            self.guardar_configuracion()
            self.logear("Las rutas de origen y destino han sido restablecidas.")
            QMessageBox.information(self, "Rutas Restablecidas", "Las rutas guardadas han sido borradas.")

    def mostrar_como_usar(self):
        """
        Show usage instructions for the translation compiler tool.
        
        This method displays a QMessageBox with detailed instructions on how to use the application,
        including selecting the source and destination folders, and processing the translations.
        It also provides warnings and tips for successful operation.
        """
        QMessageBox.information(self, "Cómo usar",
            "INSTRUCCIONES DE USO:\n\n"
            "1. Haz clic en 'Seleccionar' junto a 'Carpeta de origen' y elige la carpeta principal donde están los mods fuente.\n"
            "   - Ejemplo: C:/MisMods/Rimworld/\n"
            "   - Cada subcarpeta debe corresponder a un mod, y dentro de ella debe existir la carpeta del idioma con los archivos XML de traducción.\n"
            "   - Ejemplo de estructura:\n"
            "     C:/MisMods/Rimworld/\n"
            "      ├─ ModA\n"
            "      │   └─ Spanish (Español(Castellano))\n"
            "      │        ├─ DefInjected\n"
            "      │        └─ ...\n"
            "      └─ ModB\n"
            "          └─ Russian (Русский)\n"
            "               └─ ...\n\n"
            "2. Haz clic en 'Detectar Idiomas'. El programa buscará todas las posibles carpetas de idioma y las listará en el menú desplegable.\n\n"
            "3. Selecciona el idioma que deseas compilar en el menú 'Idioma a procesar'.\n\n"
            "4. Haz clic en 'Seleccionar' junto a 'Carpeta de destino' y elige la carpeta donde deseas copiar las traducciones (normalmente la carpeta 'Languages' de tu mod de traducción).\n"
            "   - El programa creará dentro de la carpeta de destino la subcarpeta del idioma seleccionado y copiará allí los archivos.\n\n"
            "5. Presiona el botón 'Procesar' para compilar las traducciones.\n"
            "   - Verás el progreso, un registro de actividad y la cantidad de archivos copiados.\n\n"
            "ADVERTENCIAS:\n"
            "- Asegúrate de que ningún archivo esté en uso durante la copia.\n"
            "- El nombre de la carpeta del mod (ej: ModA) será usado como prefijo para los archivos de traducción, sobreescribiendo los existentes si ya hay alguno con el mismo nombre.")

    def cargar_configuracion(self):
        default_report_config = {
            "titulo": "Reporte de Mods Procesados",
            "incluir_conteo": True,
            "incluir_lista_mods": True,
            "texto_adicional": "",
            "reporte_ruta_personalizada_enabled": False,
            "reporte_ruta_personalizada": ""
        }
        default_opciones = {
            "limpiar_destino": False,
            "eliminar_comentarios": False,
            "comprimir": False
        }
        try:
            self.origen = ''
            self.destino = ''
            self.idioma_seleccionado = ''
            # Empezar con los valores por defecto
            self.reporte_config = default_report_config.copy()
            self.opciones_default = default_opciones.copy()

            config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), CONFIG_FILE)
            if os.path.exists(config_path):
                with open(config_path, 'r', encoding='utf-8') as f:
                    datos = json.load(f)
                    self.origen = datos.get('origen', '')
                    self.destino = datos.get('destino', '')
                    self.idioma_seleccionado = datos.get('idioma_seleccionado', '')

                    # Actualizar los valores por defecto con los cargados del archivo
                    loaded_report_config = datos.get('reporte_config', {})
                    self.reporte_config.update(loaded_report_config)

                    loaded_opciones = datos.get('opciones_default', {})
                    self.opciones_default.update(loaded_opciones)

        except (json.JSONDecodeError, IOError) as e:
            # No se puede logear error aquí porque el logger no está listo
            print(f"No se pudo cargar la configuración: {e}")

    def guardar_configuracion(self):
        try:
            config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), CONFIG_FILE)
            config_data = {
                'origen': self.txt_origen.text(),
                'destino': self.txt_destino.text(),
                'idioma_seleccionado': self.cmb_idioma.currentText(),
                'reporte_config': self.reporte_config,
                'opciones_default': getattr(self, 'opciones_default', {})
            }
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(config_data, f, ensure_ascii=False, indent=2)
        except IOError as e:
            self.logear_error(f"No se pudo guardar la configuración: {e}")

    def seleccionar_origen(self):
        carpeta = QFileDialog.getExistingDirectory(self, "Selecciona carpeta 'Archivo Traducciones'")
        if carpeta:
            self.txt_origen.setText(carpeta)
            self.guardar_configuracion()
            self.detectar_idiomas()
            self.logear(f"Carpeta de origen seleccionada: {carpeta}")

    def seleccionar_destino(self):
        carpeta = QFileDialog.getExistingDirectory(self, "Selecciona carpeta raíz del Mod Pack")
        if carpeta:
            self.txt_destino.setText(carpeta)
            self.guardar_configuracion()
            self.logear(f"Carpeta de destino seleccionada: {carpeta}")

    def iniciar_proceso(self):
        # Prevenir múltiples ejecuciones simultáneas
        if hasattr(self, 'hilo') and self.hilo is not None and self.hilo.isRunning():
            QMessageBox.warning(self, "Advertencia", "Ya hay un proceso en ejecución. Por favor, espera a que termine.")
            return

        origen = self.txt_origen.text()
        destino = self.txt_destino.text()
        nombre_subcarpeta = self.cmb_idioma.currentText()

        if not origen or not destino:
            QMessageBox.warning(self, "Advertencia", "Por favor, selecciona tanto el origen como el destino.")
            return
        
        if not nombre_subcarpeta:
            QMessageBox.warning(self, "Advertencia", "Por favor, detecta y selecciona un idioma a procesar.")
            return

        # Ajuste: Usar subcarpeta Languages dentro de la raíz seleccionada
        destino_languages = os.path.join(destino, "Languages")
        if not os.path.exists(destino_languages):
            try:
                os.makedirs(destino_languages)
            except OSError as e:
                QMessageBox.critical(self, "Error", f"No se pudo crear la carpeta Languages:\n{e}")
                return

        # Validar que tenemos permisos de escritura en el destino (Languages)
        if not os.access(destino_languages, os.W_OK):
            QMessageBox.critical(self, "Error de Permisos", 
                f"No tienes permisos de escritura en la carpeta de destino:\n{destino_languages}\n\nPor favor, verifica los permisos o selecciona otra carpeta.")
            return

        limpiar = self.chk_limpiar_destino.isChecked()
        eliminar_comentarios = self.chk_eliminar_comentarios.isChecked()
        
        # Determinar nombre de destino para la advertencia de limpieza (normalizado)
        nombre_destino = normalizar_nombre_idioma(nombre_subcarpeta)

        if limpiar:
            ruta_a_borrar = os.path.join(destino_languages, nombre_destino)
            if os.path.isdir(ruta_a_borrar):
                reply = QMessageBox.question(self, 'Confirmar Limpieza',
                                             f"¿Está seguro de que desea eliminar permanentemente la carpeta y todo su contenido?\n\n{ruta_a_borrar}",
                                             QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, QMessageBox.StandardButton.No)
                if reply == QMessageBox.StandardButton.No:
                    self.logear("Proceso cancelado por el usuario.")
                    return

        self.txt_log.clear()
        self.txt_log_errores.clear()
        self.mods_procesados_en_ultimo_run = []
        self.btn_reporte.setEnabled(False)
        self.errores_widget.hide()
        self.lbl_contador_mods.setText("Mods procesados: 0")
        self.lbl_contador.setText("Archivos copiados: 0")
        self.progress.setValue(0)
        self.btn_procesar.setEnabled(False)
        self.hilo = CopiadorThread(origen, destino_languages, nombre_subcarpeta, limpiar_destino=limpiar, eliminar_comentarios=eliminar_comentarios)
        self.hilo.progreso.connect(self.progress.setValue)
        self.hilo.log.connect(self.logear)
        self.hilo.error_log.connect(self.logear_error)
        self.hilo.terminado.connect(self.proceso_terminado)
        self.hilo.mods_count.connect(self.actualizar_contador_mods)
        self.hilo.archivos_count.connect(self.actualizar_contador_archivos)
        self.hilo.start()

    def logear(self, mensaje):
        hora = datetime.now().strftime("%H:%M:%S")
        self.txt_log.append(f"[{hora}] {mensaje}")

    def logear_error(self, mensaje):
        if self.errores_widget.isHidden():
            self.errores_widget.show()
        hora = datetime.now().strftime("%H:%M:%S")
        # Agregar texto en rojo usando HTML
        self.txt_log_errores.append(f"<span style='color: #CE9178;'>[{hora}] {mensaje}</span>")

    def logear_azul(self, mensaje):
        hora = datetime.now().strftime("%H:%M:%S")
        self.txt_log.append(f"<span style='color: #569CD6;'>[{hora}] {mensaje}</span>")

    def actualizar_contador_archivos(self, cantidad):
        """Actualiza el contador de archivos copiados en la UI en tiempo real."""
        self.lbl_contador.setText(f"Archivos copiados: {cantidad}")

    def actualizar_contador_mods(self, procesados, total):
        self.lbl_contador_mods.setText(f"Mods procesados: {procesados}/{total}")

    def proceso_terminado(self, cantidad):
        self.lbl_contador.setText(f"Archivos copiados: {cantidad}")
        self.progress.setValue(100)
        # Verificar que self.hilo no sea None antes de acceder a sus atributos
        if self.hilo is not None:
            self.mods_procesados_en_ultimo_run = self.hilo.mods_procesados
        else:
            self.mods_procesados_en_ultimo_run = []

        if cantidad > 0 and self.mods_procesados_en_ultimo_run:
            self.btn_reporte.setEnabled(True)

        if cantidad > 0 and self.chk_update_about.isChecked():
            self.actualizar_about_xml()

        if cantidad > 0 and self.chk_comprimir.isChecked():
            self.iniciar_compresion()
        else:
            self.btn_procesar.setEnabled(True)
            msg = f"Se han copiado {cantidad} archivos correctamente."
            if cantidad == 0:
                msg = "No se encontraron archivos XML para copiar."
            
            if not self.chk_comprimir.isChecked() and cantidad > 0:
                self.logear("Compresión no solicitada. Proceso finalizado.")

            QMessageBox.information(self, "Proceso Completado", msg)

    def iniciar_compresion(self):
        self.logear("Iniciando proceso de compresión...")
        destino_root = self.txt_destino.text()
        destino_languages = os.path.join(destino_root, "Languages")
        # Usar el nombre de destino procesado por el hilo de copia
        if self.hilo is not None:
            nombre_subcarpeta = self.hilo.nombre_destino
        else:
            # Fallback si por alguna razón self.hilo es None
            nombre_subcarpeta = normalizar_nombre_idioma(self.cmb_idioma.currentText())
        self.compresor_hilo = CompresorThread(destino_languages, nombre_subcarpeta)
        self.compresor_hilo.log.connect(self.logear)
        self.compresor_hilo.error_log.connect(self.logear_error)
        self.compresor_hilo.terminado.connect(self.compresion_terminada)
        self.compresor_hilo.start()

    def compresion_terminada(self, exito, mensaje):
        self.btn_procesar.setEnabled(True)
        # Verificar que self.hilo no sea None antes de acceder a sus atributos
        cantidad_copiados = self.hilo.archivos_copiados if self.hilo is not None else 0
        if exito:
            msg_final = (f"Se han copiado {cantidad_copiados} archivos correctamente.\n\n"
                         f"El archivo .tar ha sido creado exitosamente en:\n{mensaje}")
            QMessageBox.information(self, "Proceso Completado", msg_final)
        else:
            msg_final = (f"Se han copiado {cantidad_copiados} archivos correctamente, "
                         f"pero ocurrió un error al comprimir:\n{mensaje}")
            QMessageBox.critical(self, "Error de Compresión", msg_final)

    def generar_reporte(self):
        if not self.mods_procesados_en_ultimo_run:
            QMessageBox.information(self, "Reporte", "No hay información de mods para generar un reporte. Por favor, ejecute el proceso primero.")
            return

        destino = self.txt_destino.text()
        if not destino or not os.path.isdir(destino):
            QMessageBox.warning(self, "Advertencia", "La carpeta de destino no es válida. No se puede generar el reporte.")
            return

        cfg = self.reporte_config
        ruta_reportes = ""

        # Determinar la ruta para guardar el reporte
        if cfg.get("reporte_ruta_personalizada_enabled", False) and cfg.get("reporte_ruta_personalizada", ""):
            ruta_reportes = cfg.get("reporte_ruta_personalizada", "")
            if not ruta_reportes or not os.path.isdir(ruta_reportes):
                QMessageBox.warning(self, "Advertencia", f"La ruta de reporte personalizada no es válida:\n{ruta_reportes}\n\nSe usará la carpeta por defecto.")
                ruta_reportes = ""  # Volver al valor por defecto

        if not ruta_reportes:
            ruta_reportes = os.path.join(destino, "Reportes")

        try:
            # Crear carpeta de reportes
            os.makedirs(ruta_reportes, exist_ok=True)

            # Crear nombre de archivo con timestamp
            timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            nombre_archivo = f"reporte_mods_{timestamp}.txt"
            ruta_archivo = os.path.join(ruta_reportes, nombre_archivo)

            # Escribir el reporte usando la configuración
            with open(ruta_archivo, 'w', encoding='utf-8') as f:
                f.write(f"{cfg.get('titulo', 'Reporte de Mods Procesados')} - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write("="*50 + "\n")

                if cfg.get('texto_adicional', ''):
                    f.write(f"\n{cfg['texto_adicional']}\n\n")

                if cfg.get('incluir_conteo', True):
                    f.write(f"Total de mods encontrados: {len(self.mods_procesados_en_ultimo_run)}\n\n")

                if cfg.get('incluir_lista_mods', True):
                    f.write("Lista de mods:\n")
                    for mod in sorted(self.mods_procesados_en_ultimo_run):
                        f.write(f"- {mod}\n")

            self.logear(f"Reporte generado exitosamente en: {ruta_archivo}")
            QMessageBox.information(self, "Reporte Generado", f"El reporte ha sido guardado en:\n{ruta_archivo}")

            # Abrir la carpeta de reportes
            if sys.platform == "win32":
                os.startfile(ruta_reportes)
            elif sys.platform == "darwin":
                subprocess.Popen(["open", ruta_reportes])
            else:
                subprocess.Popen(["xdg-open", ruta_reportes])
        except Exception as e:
            error_msg = f"Ocurrió un error al generar el reporte: {e}"
            self.logear_error(error_msg)
            QMessageBox.critical(self, "Error de Reporte", error_msg)

    def detectar_idiomas(self):
        origen = self.txt_origen.text()
        if not origen or not os.path.isdir(origen):
            self.cmb_idioma.clear()
            self.cmb_idioma.setEnabled(False)
            return

        self.logear("Detectando posibles carpetas de idioma...")
        idiomas_encontrados = set()
        total_xml_files = 0
        # Carpetas a ignorar que comúnmente no son de idiomas
        carpetas_a_ignorar = {'about', 'defs', 'assemblies', 'patches', 'textures', 'sounds', 'common', 'ideasshared', 'licenses', 'source', 'src', 'docs', 'examples', '.git', '.vs', '1.0', '1.1', '1.2', '1.3', '1.4', '1.5'}

        try:
            mod_folders = [d for d in os.listdir(origen) if os.path.isdir(os.path.join(origen, d))]
            if not mod_folders:
                self.logear("No se encontraron carpetas de mods en el origen.")
                return

            for mod_folder in mod_folders:
                ruta_mod = os.path.join(origen, mod_folder)
                try:
                    for subfolder in os.listdir(ruta_mod):
                        ruta_subfolder = os.path.join(ruta_mod, subfolder)
                        if os.path.isdir(ruta_subfolder) and subfolder.lower() not in carpetas_a_ignorar:
                            idiomas_encontrados.add(subfolder)
                            for _, _, archivos in os.walk(ruta_subfolder):
                                total_xml_files += sum(1 for archivo in archivos if archivo.endswith(".xml"))
                except OSError:
                    continue # Ignorar si no se puede acceder

            self.cmb_idioma.clear()
            if idiomas_encontrados:
                sorted_idiomas = sorted(list(idiomas_encontrados))
                self.cmb_idioma.addItems(sorted_idiomas)
                self.cmb_idioma.setEnabled(True)
                self.logear(f"Carpetas detectadas: {len(sorted_idiomas)}, con {total_xml_files} archivos XML. Por favor, selecciona el idioma a procesar.")
                if self.idioma_seleccionado and self.idioma_seleccionado in sorted_idiomas:
                    self.cmb_idioma.setCurrentText(self.idioma_seleccionado)
            else:
                self.logear("No se detectaron carpetas que parezcan ser de idioma.")
                self.cmb_idioma.setEnabled(False)
        except Exception as e:
            self.logear_error(f"Error al detectar idiomas: {e}")

    def aplicar_opciones_default(self):
        if hasattr(self, 'opciones_default'):
            self.chk_limpiar_destino.setChecked(self.opciones_default.get('limpiar_destino', False))
            self.chk_eliminar_comentarios.setChecked(self.opciones_default.get('eliminar_comentarios', False))
            self.chk_comprimir.setChecked(self.opciones_default.get('comprimir', False))
            self.chk_update_about.setChecked(self.opciones_default.get('update_about', False))

    def mostrar_acerca_de(self):
        QMessageBox.information(self, "Acerca de",
            "Compilador de Traducciones\n\n"
            "Versión PySide6\n"
            "Herramienta para compilar y organizar archivos de traducción de mods.\n\n"
            "Desarrollado por Mordelon con la asistencia de Gemini.\n\n"
            "© 2025 Todos los derechos reservados.")

    def actualizar_about_xml(self):
        destino = self.txt_destino.text()
        # Intentar localizar about.xml en ./About/about.xml (asumiendo destino=Root)
        # o ../About/about.xml (asumiendo destino=Languages por compatibilidad)
        
        rutas_posibles = [
            os.path.join(destino, "About", "about.xml"),
            os.path.join(os.path.dirname(destino), "About", "about.xml")
        ]
        
        ruta_about = None
        for r in rutas_posibles:
            if os.path.isfile(r):
                ruta_about = r
                break
        
        if not ruta_about:
            self.logear("No se encontró 'About/about.xml' para actualizar la lista de mods.")
            return

        self.logear(f"Actualizando lista de mods en: {ruta_about}")
        
        try:
            # Parsear about.xml
            tree = ET.parse(ruta_about)
            root = tree.getroot()
            
            # Buscar forceLoadAfter
            force_load = root.find('forceLoadAfter')
            if force_load is None:
                force_load = ET.SubElement(root, 'forceLoadAfter')
            
            # Limpiar lista actual
            force_load.clear()
            
            # Recopilar IDs
            origen = self.txt_origen.text()
            ids_mods = []
            
            for mod_name in self.mods_procesados_en_ultimo_run:
                ruta_mod = os.path.join(origen, mod_name)
                pid = self.obtener_package_id(ruta_mod)
                
                # Verificar si existe PublishedFileId.txt
                has_published_id = False
                for p in [os.path.join(ruta_mod, "PublishedFileId.txt"), os.path.join(ruta_mod, "About", "PublishedFileId.txt")]:
                    if os.path.isfile(p):
                        has_published_id = True
                        break
                
                if not pid or not has_published_id:
                    self.logear_azul(f"Faltan metadatos en: {mod_name}")
                else:
                    ids_mods.append(pid)
            
            # Ordenar y eliminar duplicados
            ids_mods = sorted(list(set(ids_mods)))
            
            # Rellenar forceLoadAfter
            for pid in ids_mods:
                li = ET.SubElement(force_load, 'li')
                li.text = pid
            
            # Re-indentar para que quede bonito
            indent_xml(root)
            
            tree.write(ruta_about, encoding='utf-8', xml_declaration=True)
            self.logear(f"About.xml actualizado correctamente con {len(ids_mods)} entradas.")
            
        except Exception as e:
            self.logear_error(f"Error al actualizar about.xml: {e}")

    def obtener_package_id(self, ruta_mod):
        about_dir = os.path.join(ruta_mod, "About")
        if not os.path.isdir(about_dir):
            return None
            
        # Buscar cualquier archivo XML que empiece por About (ej: About.xml, About_12345.xml)
        candidatos = [f for f in os.listdir(about_dir) if f.lower().startswith("about") and f.lower().endswith(".xml")]
        
        # Ordenar para preferir 'About.xml' (más corto) si existe, o el primero que encuentre
        candidatos.sort(key=len)
        
        for nombre in candidatos:
            ruta = os.path.join(ruta_mod, "About", nombre)
            try:
                tree = ET.parse(ruta)
                root = tree.getroot()
                pid = root.find("packageId")
                if pid is not None and pid.text:
                    return pid.text.strip().lower()
            except:
                continue
        return None

if __name__ == "__main__":
    app = QApplication(sys.argv)
    ventana = VentanaPrincipal()
    ventana.aplicar_opciones_default()
    ventana.show()
    sys.exit(app.exec())
