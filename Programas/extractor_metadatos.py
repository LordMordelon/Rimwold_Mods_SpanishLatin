import sys
import os
import re
import xml.etree.ElementTree as ET
from xml.sax.saxutils import escape
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QLabel, QLineEdit, QPushButton, 
                             QTextEdit, QFileDialog, QMessageBox, QProgressBar)
from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtGui import QFont

# Ruta por defecto de los mods de RimWorld en Steam Workshop
DEFAULT_WORKSHOP_PATH = r"C:\Program Files (x86)\Steam\steamapps\workshop\content\294100"

def sanitize_filename(name):
    """Limpia el nombre para que sea válido como nombre de carpeta en Windows."""
    if not name:
        return "Unnamed_Mod"
    # Eliminar dos puntos
    cleaned = name.replace(':', '')
    # Reemplazar otros caracteres no válidos en Windows: < > " / \ | ? *
    cleaned = re.sub(r'[<>"/\\|?*]', '_', cleaned).strip()
    # Eliminar puntos al final (Windows no los quiere)
    cleaned = cleaned.rstrip('.')
    return cleaned if cleaned else "Unnamed_Mod"

class ExtractorThread(QThread):
    progress = Signal(int)
    log = Signal(str)
    finished = Signal(str)

    def __init__(self, source_dir, dest_dir):
        super().__init__()
        self.source_dir = source_dir
        self.dest_dir = dest_dir
        self.is_running = True

    def run(self):
        if not os.path.exists(self.source_dir):
            self.finished.emit(f"Error: La carpeta de origen no existe: {self.source_dir}")
            return

        self.log.emit("Escaneando carpeta de Workshop...")
        
        # Listar subdirectorios
        try:
            subdirs = [d for d in os.listdir(self.source_dir) if os.path.isdir(os.path.join(self.source_dir, d))]
        except Exception as e:
            self.finished.emit(f"Error al leer directorio: {e}")
            return

        # Filtrar solo carpetas numéricas (IDs de Workshop)
        workshop_ids = [d for d in subdirs if d.isdigit()]
        
        total = len(workshop_ids)
        if total == 0:
            self.finished.emit("No se encontraron carpetas de mods (IDs numéricos) en la ruta seleccionada.")
            return

        processed_count = 0
        errors = 0
        skipped = 0

        self.log.emit(f"Se encontraron {total} carpetas de mods. Iniciando extracción de metadatos...")

        # Crear carpeta raíz Metadatos_Mods
        output_root = os.path.join(self.dest_dir, "Metadatos_Mods")
        try:
            os.makedirs(output_root, exist_ok=True)
        except Exception as e:
            self.finished.emit(f"Error creando carpeta Metadatos_Mods: {e}")
            return

        for i, mod_id in enumerate(workshop_ids):
            if not self.is_running:
                self.log.emit("Proceso detenido por el usuario.")
                break
            
            mod_path = os.path.join(self.source_dir, mod_id)
            about_dir_source = os.path.join(mod_path, "About")
            
            # Buscar About.xml (puede ser About.xml o about.xml)
            about_xml_path = os.path.join(about_dir_source, "About.xml")
            if not os.path.exists(about_xml_path):
                about_xml_path = os.path.join(about_dir_source, "about.xml")

            if os.path.exists(about_xml_path):
                try:
                    # Parsear el XML original para obtener datos
                    tree = ET.parse(about_xml_path)
                    root = tree.getroot()
                    
                    name_node = root.find("name")
                    author_node = root.find("author")
                    package_id_node = root.find("packageId")
                    
                    # Obtener valores o usar defaults
                    mod_name = name_node.text if name_node is not None and name_node.text else f"Unknown Mod {mod_id}"
                    author = author_node.text if author_node is not None and author_node.text else "Unknown"
                    package_id = package_id_node.text if package_id_node is not None and package_id_node.text else "Unknown.PackageId"
                    
                    # Sanitizar nombre para crear carpeta de destino
                    folder_name = sanitize_filename(mod_name)
                    
                    # Crear estructura destino: Destino / Metadatos_Mods / NombreMod / About
                    dest_mod_path = os.path.join(output_root, folder_name)
                    dest_about_path = os.path.join(dest_mod_path, "About")
                    os.makedirs(dest_about_path, exist_ok=True)
                    
                    # 1. Crear PublishedFileId.txt
                    with open(os.path.join(dest_about_path, "PublishedFileId.txt"), "w", encoding="utf-8") as f:
                        f.write(mod_id)
                        
                    # 2. Crear About.xml con el formato solicitado
                    # Construimos el string manualmente para garantizar el formato exacto y los comentarios
                    xml_content = (
                        "<ModMetaData>\n"
                        f"\t<name>{escape(mod_name)}</name>\n"
                        f"\t<author>{escape(author)}</author>\n"
                        f"\t<packageId>{escape(package_id)}</packageId>\n"
                        f"\t<!-- PublishedFileId: {mod_id} -->\n"
                        "</ModMetaData>"
                    )
                    
                    about_filename = f"About_{mod_id}.xml"
                    with open(os.path.join(dest_about_path, about_filename), "w", encoding="utf-8") as f:
                        f.write(xml_content)
                        
                    self.log.emit(f"Extraído: {mod_name} ({mod_id})")
                    processed_count += 1
                    
                except Exception as e:
                    self.log.emit(f"Error procesando {mod_id}: {str(e)}")
                    errors += 1
            else:
                # Si no hay About.xml, no es un mod válido o tiene estructura rara
                skipped += 1

            # Actualizar barra de progreso
            progress_percent = int((i + 1) / total * 100)
            self.progress.emit(progress_percent)

        msg_final = (f"Proceso finalizado.\n"
                     f"Mods procesados: {processed_count}\n"
                     f"Saltados (sin About.xml): {skipped}\n"
                     f"Errores: {errors}")
        self.finished.emit(msg_final)

    def stop(self):
        self.is_running = False

class MetadataExtractorGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Extractor de Metadatos RimWorld")
        self.setGeometry(100, 100, 700, 500)
        self.worker = None
        self.init_ui()

    def init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)

        # Título
        lbl_title = QLabel("Extractor de Metadatos de Workshop")
        lbl_title.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        lbl_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(lbl_title)

        # Origen (Workshop)
        layout.addWidget(QLabel("Carpeta de Mods (Steam Workshop):"))
        h_source = QHBoxLayout()
        self.txt_source = QLineEdit()
        # Intentar poner la ruta por defecto si existe
        if os.path.exists(DEFAULT_WORKSHOP_PATH):
            self.txt_source.setText(DEFAULT_WORKSHOP_PATH)
        
        btn_source = QPushButton("Seleccionar")
        btn_source.clicked.connect(self.select_source)
        h_source.addWidget(self.txt_source)
        h_source.addWidget(btn_source)
        layout.addLayout(h_source)

        # Destino
        layout.addWidget(QLabel("Carpeta de Destino (Donde se guardarán los metadatos):"))
        h_dest = QHBoxLayout()
        self.txt_dest = QLineEdit()
        btn_dest = QPushButton("Seleccionar")
        btn_dest.clicked.connect(self.select_dest)
        h_dest.addWidget(self.txt_dest)
        h_dest.addWidget(btn_dest)
        layout.addLayout(h_dest)

        # Botón Acción
        self.btn_run = QPushButton("Extraer Metadatos")
        self.btn_run.setMinimumHeight(40)
        self.btn_run.setStyleSheet("font-weight: bold; font-size: 12px;")
        self.btn_run.clicked.connect(self.start_extraction)
        layout.addWidget(self.btn_run)

        # Progreso
        self.progress_bar = QProgressBar()
        layout.addWidget(self.progress_bar)

        # Log
        layout.addWidget(QLabel("Registro:"))
        self.txt_log = QTextEdit()
        self.txt_log.setReadOnly(True)
        layout.addWidget(self.txt_log)

    def select_source(self):
        dir_path = QFileDialog.getExistingDirectory(self, "Seleccionar carpeta Workshop (294100)")
        if dir_path:
            self.txt_source.setText(dir_path)

    def select_dest(self):
        dir_path = QFileDialog.getExistingDirectory(self, "Seleccionar carpeta de Destino")
        if dir_path:
            self.txt_dest.setText(dir_path)

    def log(self, message):
        self.txt_log.append(message)

    def start_extraction(self):
        source = self.txt_source.text()
        dest = self.txt_dest.text()

        if not source or not os.path.exists(source):
            QMessageBox.warning(self, "Error", "La carpeta de origen no es válida.")
            return
        if not dest or not os.path.exists(dest):
            QMessageBox.warning(self, "Error", "La carpeta de destino no es válida.")
            return

        self.btn_run.setEnabled(False)
        self.txt_log.clear()
        self.progress_bar.setValue(0)

        self.worker = ExtractorThread(source, dest)
        self.worker.log.connect(self.log)
        self.worker.progress.connect(self.progress_bar.setValue)
        self.worker.finished.connect(self.process_finished)
        self.worker.start()

    def process_finished(self, message):
        self.btn_run.setEnabled(True)
        QMessageBox.information(self, "Proceso Terminado", message)
        self.log("--- Fin del proceso ---")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MetadataExtractorGUI()
    window.show()
    sys.exit(app.exec())