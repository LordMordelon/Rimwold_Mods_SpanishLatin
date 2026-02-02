import sys
import os
import shutil
import json
import re
import xml.etree.ElementTree as ET
from pathlib import Path
from xml.sax.saxutils import escape
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QLabel, QLineEdit, QPushButton, 
                             QTextEdit, QFileDialog, QMessageBox, QToolButton, QMenu, QComboBox)
from PySide6.QtGui import QAction, QDesktopServices
from PySide6.QtCore import Qt, QUrl

class RimWorldTranslatorGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("RimWorld Translation Extractor")
        self.setMinimumSize(600, 400)

        # Archivo de configuración en el directorio del script (Desktop)
        self.config_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "extractor_config.json")

        # Etiquetas que normalmente queremos traducir
        self.translatable_tags = [
            'label', 'description', 'jobString', 'reportString', 'pawnLabel', 
            'graphLabel', 'verb', 'gerund', 'deathMessage', 'skillLabel', 
            'labelNoun', 'labelShort', 'labelPlural', 'adjective', 'text', 
            'rejectionMessage', 'helpText', 'labelShortAdj', 'flavorText',
            'title', 'titleShort', 'baseDesc', 'titleFemale', 'titleShortFemale',
            'letterLabel', 'letterText', 'extraOutcomeDesc',
            'customLabel', 'chargeNoun', 'endMessage'
        ]

        # Etiquetas técnicas a excluir (blacklist)
        self.blacklisted_tags = [
            'verbClass', 'commandTexture', 'commandLabelKey', 'texPath', 'iconPath'
        ]

        self.init_ui()
        self.load_config()

    def init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)
        
        # Layout izquierdo (controles principales)
        left_layout = QVBoxLayout()
        
        # Layout derecho (etiquetas editables)
        right_layout = QVBoxLayout()
        
        main_layout.addLayout(left_layout, stretch=3)
        main_layout.addLayout(right_layout, stretch=1)
        
        layout = left_layout  # Mantener compatibilidad con el resto del código

        # Selección de carpeta del Mod
        defs_layout = QHBoxLayout()
        self.defs_input = QLineEdit()
        self.defs_input.setPlaceholderText("Ruta de la carpeta del Mod")
        
        # Auto-detectar si el script está dentro de la carpeta del mod
        script_dir = os.path.dirname(os.path.abspath(__file__))
        
        # Si encontramos 'Defs' en profundidad (estamos en un Mod)
        if any("Defs" in dirs for _, dirs, _ in os.walk(script_dir)):
            self.defs_input.setText(script_dir)

        btn_browse = QPushButton("Buscar...")
        btn_browse.clicked.connect(self.browse_mod)
        btn_open_mod = QPushButton("Abrir")
        btn_open_mod.clicked.connect(lambda: self.open_folder(self.defs_input.text()))
        defs_layout.addWidget(QLabel("Carpeta del Mod:"))
        defs_layout.addWidget(self.defs_input)
        defs_layout.addWidget(btn_browse)
        defs_layout.addWidget(btn_open_mod)
        layout.addLayout(defs_layout)

        # Selección de carpeta de Archivo de Traducciones (Repositorio)
        archive_layout = QHBoxLayout()
        self.archive_input = QLineEdit()
        self.archive_input.setPlaceholderText("Ruta del Archivo de Traducciones (Opcional)")
        btn_browse_archive = QPushButton("Buscar Archivo...")
        btn_browse_archive.clicked.connect(self.browse_archive)
        btn_open_archive = QPushButton("Abrir")
        btn_open_archive.clicked.connect(lambda: self.open_folder(self.archive_input.text()))
        archive_layout.addWidget(QLabel("Archivo Traducciones:"))
        archive_layout.addWidget(self.archive_input)
        archive_layout.addWidget(btn_browse_archive)
        archive_layout.addWidget(btn_open_archive)
        layout.addLayout(archive_layout)

        # Nombre del lenguaje
        lang_layout = QHBoxLayout()
        self.lang_input = QLineEdit("SpanishLatin")
        lang_layout.addWidget(QLabel("Lenguaje de salida:"))
        lang_layout.addWidget(self.lang_input)
        
        self.version_combo = QComboBox()
        self.version_combo.addItems(["Todas", "1.6", "1.5", "1.4", "1.3", "1.2", "1.1", "1.0", "Base"])
        lang_layout.addWidget(QLabel("Versión:"))
        lang_layout.addWidget(self.version_combo)
        layout.addLayout(lang_layout)

        # Opciones en menú desplegable
        opts_layout = QHBoxLayout()
        self.btn_options = QPushButton("Opciones")
        
        self.opts_menu = QMenu(self)
        self.opts_menu.setToolTipsVisible(True)
        self.act_popup = QAction("Mostrar aviso al finalizar", self)
        self.act_popup.setCheckable(True)
        self.act_popup.setChecked(True)
        self.act_popup.setToolTip("Muestra una ventana emergente confirmando que el proceso ha terminado.")
        self.act_readme = QAction("Crear archivo LEEME", self)
        self.act_readme.setCheckable(True)
        self.act_readme.setChecked(True)
        self.act_readme.setToolTip("Genera un archivo de texto con instrucciones de instalación en la carpeta de salida.")
        self.act_merge = QAction("Combinar todo en versión destino", self)
        self.act_merge.setCheckable(True)
        self.act_merge.setChecked(False)
        self.act_merge.setToolTip("Fusiona el contenido de todas las versiones encontradas dentro de la carpeta de la versión seleccionada.")
        self.act_simplify_mods = QAction("Integrar contenido de Mods en raíz", self)
        self.act_simplify_mods.setCheckable(True)
        self.act_simplify_mods.setChecked(False)
        self.act_simplify_mods.setToolTip("Elimina la estructura de carpetas 'Mods/NombreMod' y mueve todo el contenido directamente a la carpeta principal.")
        self.act_clean = QAction("Limpiar carpeta de salida", self)
        self.act_clean.setCheckable(True)
        self.act_clean.setChecked(False)
        self.act_clean.setToolTip("Elimina la carpeta de destino antes de generar los archivos para asegurar una extracción limpia.")
        self.act_recover_implicit = QAction("Recuperar líneas implícitas (Legacy)", self)
        self.act_recover_implicit.setCheckable(True)
        self.act_recover_implicit.setChecked(False)
        self.act_recover_implicit.setToolTip("Intenta recuperar traducciones de líneas que no están en el XML (ej. deathMessage heredado) usando el archivo y validando con el inglés.")
        self.act_create_about = QAction("Crear About.xml (Metadata)", self)
        self.act_create_about.setCheckable(True)
        self.act_create_about.setChecked(True)
        self.act_create_about.setToolTip("Genera una carpeta About con un archivo About.xml mínimo (nombre, autor, packageId) extraído del mod original.")
        
        self.opts_menu.addAction(self.act_popup)
        self.opts_menu.addAction(self.act_readme)
        self.opts_menu.addAction(self.act_merge)
        self.opts_menu.addAction(self.act_simplify_mods)
        self.opts_menu.addAction(self.act_clean)
        self.opts_menu.addAction(self.act_recover_implicit)
        self.opts_menu.addAction(self.act_create_about)
        self.btn_options.setMenu(self.opts_menu)
        
        opts_layout.addWidget(self.btn_options)
        opts_layout.addStretch()
        layout.addLayout(opts_layout)

        # Botón principal
        self.btn_run = QPushButton("Generar Archivos de Traducción")
        self.btn_run.setStyleSheet("background-color: #2c3e50; color: white; font-weight: bold; padding: 10px;")
        self.btn_run.clicked.connect(self.run_extraction)
        layout.addWidget(self.btn_run)

        # Área de log
        self.log_output = QTextEdit()
        self.log_output.setReadOnly(True)
        self.log_output.setStyleSheet("background-color: #1e1e1e; color: #d4d4d4; font-family: Consolas;")
        layout.addWidget(self.log_output)
        
        # --- Panel derecho: Etiquetas editables ---
        right_layout.addWidget(QLabel("<b>Etiquetas Traducibles:</b>"))
        self.translatable_input = QTextEdit()
        self.translatable_input.setPlaceholderText("Separadas por comas: label, description, ...")
        self.translatable_input.setMaximumHeight(200)
        right_layout.addWidget(self.translatable_input)
        
        right_layout.addWidget(QLabel("<b>Etiquetas Excluidas:</b>"))
        self.blacklist_input = QTextEdit()
        self.blacklist_input.setPlaceholderText("Separadas por comas: verbClass, texPath, ...")
        self.blacklist_input.setMaximumHeight(200)
        right_layout.addWidget(self.blacklist_input)
        
        # Botón para reestablecer valores por defecto
        btn_reset_tags = QPushButton("Restablecer por defecto")
        btn_reset_tags.clicked.connect(self.reset_default_tags)
        right_layout.addWidget(btn_reset_tags)
        
        right_layout.addStretch()
        
        # Cargar valores iniciales en los cuadros
        self.load_tags_to_ui()

    def open_folder(self, path):
        if path and os.path.exists(path):
            QDesktopServices.openUrl(QUrl.fromLocalFile(path))
        else:
            QMessageBox.warning(self, "Aviso", "La ruta no existe o está vacía.")
    
    def load_tags_to_ui(self):
        """Cargar las listas de etiquetas en los cuadros de texto"""
        self.translatable_input.setPlainText(", ".join(self.translatable_tags))
        self.blacklist_input.setPlainText(", ".join(self.blacklisted_tags))
    
    def update_tags_from_ui(self):
        """Actualizar las listas desde los cuadros de texto"""
        translatable_text = self.translatable_input.toPlainText()
        blacklist_text = self.blacklist_input.toPlainText()
        
        # Parsear separando por comas y limpiando espacios
        self.translatable_tags = [tag.strip() for tag in translatable_text.split(',') if tag.strip()]
        self.blacklisted_tags = [tag.strip() for tag in blacklist_text.split(',') if tag.strip()]
    
    def reset_default_tags(self):
        """Restablecer las etiquetas a los valores por defecto"""
        self.translatable_tags = [
            'label', 'description', 'jobString', 'reportString', 'pawnLabel', 
            'graphLabel', 'verb', 'gerund', 'deathMessage', 'skillLabel', 
            'labelNoun', 'labelShort', 'labelPlural', 'adjective', 'text', 
            'rejectionMessage', 'helpText', 'labelShortAdj', 'flavorText',
            'title', 'titleShort', 'baseDesc', 'titleFemale', 'titleShortFemale',
            'letterLabel', 'letterText', 'extraOutcomeDesc',
            'customLabel', 'chargeNoun', 'endMessage'
        ]
        self.blacklisted_tags = [
            'verbClass', 'commandTexture', 'commandLabelKey', 'texPath', 'iconPath'
        ]
        self.load_tags_to_ui()
        QMessageBox.information(self, "Restablecido", "Las etiquetas han sido restablecidas a los valores por defecto.")

    def browse_mod(self):
        start_dir = self.defs_input.text() or os.path.dirname(os.path.abspath(__file__))
        directory = QFileDialog.getExistingDirectory(self, "Seleccionar carpeta del Mod", start_dir)
        if directory:
            self.defs_input.setText(directory)

    def browse_archive(self):
        directory = QFileDialog.getExistingDirectory(self, "Seleccionar carpeta de Archivo de Traducciones")
        if directory:
            self.archive_input.setText(directory)

    def log(self, message):
        self.log_output.append(message)

    def load_config(self):
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r') as f:
                    config = json.load(f)
                    last_path = config.get('last_mod_path', '')
                    if last_path and os.path.exists(last_path):
                        self.defs_input.setText(last_path)
                    archive_path = config.get('archive_path', '')
                    if archive_path and os.path.exists(archive_path):
                        self.archive_input.setText(archive_path)
                    version = config.get('target_version', 'Todas')
                    idx = self.version_combo.findText(version)
                    if idx >= 0: self.version_combo.setCurrentIndex(idx)
                    self.act_popup.setChecked(config.get('show_popup', True))
                    self.act_readme.setChecked(config.get('create_readme', True))
                    self.act_merge.setChecked(config.get('merge_versions', False))
                    self.act_simplify_mods.setChecked(config.get('simplify_mods', False))
                    self.act_clean.setChecked(config.get('clean_output', False))
                    self.act_recover_implicit.setChecked(config.get('recover_implicit', False))
                    self.act_create_about.setChecked(config.get('create_about', True))
                    
                    # Cargar etiquetas personalizadas si existen
                    if 'translatable_tags' in config:
                        self.translatable_tags = config['translatable_tags']
                    if 'blacklisted_tags' in config:
                        self.blacklisted_tags = config['blacklisted_tags']
            except Exception:
                pass

    def save_config(self):
        try:
            # Actualizar etiquetas desde la UI
            self.update_tags_from_ui()
            
            config = {
                'last_mod_path': self.defs_input.text(),
                'archive_path': self.archive_input.text(),
                'target_version': self.version_combo.currentText(),
                'show_popup': self.act_popup.isChecked(),
                'create_readme': self.act_readme.isChecked(),
                'merge_versions': self.act_merge.isChecked(),
                'simplify_mods': self.act_simplify_mods.isChecked(),
                'clean_output': self.act_clean.isChecked(),
                'recover_implicit': self.act_recover_implicit.isChecked(),
                'create_about': self.act_create_about.isChecked(),
                'translatable_tags': self.translatable_tags,
                'blacklisted_tags': self.blacklisted_tags
            }
            with open(self.config_file, 'w') as f:
                json.dump(config, f, indent=2)
        except Exception:
            pass

    def load_archive_translations(self, archive_path):
        translations = {}
        if archive_path and archive_path.exists():
            # self.log(f"Indexando referencias desde: {archive_path}...")
            count = 0
            for arch_file in archive_path.rglob("*.xml"):
                try:
                    tree = ET.parse(arch_file)
                    root = tree.getroot()
                    for child in root:
                        if child.tag and child.text:
                            text = child.text.strip()
                            if text and text.upper() != "TODO":
                                translations[child.tag] = text
                                count += 1
                except Exception as e:
                    self.log(f"Advertencia: No se pudo leer referencia {arch_file.name}: {e}")
            self.log(f"Referencias cargadas desde archivo")
        return translations

    def load_single_xml_translations(self, file_path):
        translations = {}
        try:
            tree = ET.parse(file_path)
            root = tree.getroot()
            for child in root:
                if child.tag and child.text:
                    text = child.text.strip()
                    if text and text.upper() != "TODO":
                        translations[child.tag] = text
        except Exception:
            pass
        return translations

    def run_extraction(self):
        # Actualizar las etiquetas desde la UI antes de procesar
        self.update_tags_from_ui()
        
        self.save_config()
        mod_path = Path(self.defs_input.text())
        output_lang = self.lang_input.text()
        target_version = self.version_combo.currentText()
        merge_versions = self.act_merge.isChecked()
        simplify_mods = self.act_simplify_mods.isChecked()
        
        # Carpeta centralizada de salida: Mod/Plantillas Traducciones/SpanishLatin
        output_root = mod_path / "Plantillas Traducciones" / output_lang

        self.log_output.clear()
        
        if self.act_clean.isChecked() and output_root.exists():
            try:
                shutil.rmtree(output_root)
                self.log(f"Carpeta de salida limpiada: {output_root}")
            except Exception as e:
                self.log(f"Error al limpiar carpeta de salida: {e}")

        self.log("============================================================")
        self.log(f" Plantilla Traduccion: {mod_path.name}")
        self.log(f" Idioma destino: {output_lang}")
        self.log("============================================================")
        self.log("")
        
        # --- Buscar carpeta de referencia en el Archivo ---
        archive_lang_path = None
        archive_root_str = self.archive_input.text()
        if archive_root_str and os.path.exists(archive_root_str):
            mod_dir_name = mod_path.name
            candidate_mod = Path(archive_root_str) / mod_dir_name
            
            if candidate_mod.exists():
                # Buscar la carpeta del idioma dentro del mod en el archivo
                # Estrategia: Buscar coincidencia exacta o carpeta que empiece por el idioma
                search_dirs = [candidate_mod]
                if (candidate_mod / "Languages").exists():
                    search_dirs.append(candidate_mod / "Languages")
                
                found = False
                for search_dir in search_dirs:
                    for item in search_dir.iterdir():
                        if item.is_dir() and item.name.lower().startswith(output_lang.lower()):
                            archive_lang_path = item
                            found = True
                            break
                    if found: break
                
                if archive_lang_path:
                    pass # self.log(f"Referencia encontrada en archivo: {archive_lang_path}")
                else:
                    self.log(f"Aviso: Mod encontrado en archivo, pero no el idioma '{output_lang}'.")
            else:
                pass # self.log(f"No se encontró el mod '{mod_dir_name}' en la carpeta de archivo.")

        # Cargar traducciones globales una sola vez y limpias de TODOs
        self.global_archive_translations = {}
        if archive_lang_path:
            self.global_archive_translations = self.load_archive_translations(archive_lang_path)

        # Cargar traducciones en INGLÉS para validar implícitos
        self.english_translations = {}
        if self.act_recover_implicit.isChecked():
            english_dirs = [mod_path / "Languages" / "English", mod_path / "Languages" / "English (United Kingdom)"]
            for eng_dir in english_dirs:
                if eng_dir.exists():
                    self.log(f"Cargando fuente en Inglés desde: {eng_dir.name}...")
                    self.english_translations = self.load_archive_translations(eng_dir)
                    break

        try:
            # --- 1. Procesar DEFS ---
            defs_directories = []
            for root, dirs, files in os.walk(mod_path):
                if os.path.basename(root).lower() == 'defs':
                    defs_directories.append(Path(root))

            # Ordenar para que las versiones salgan en orden (1.3, 1.4, 1.5...)
            defs_directories.sort(key=lambda p: str(p))

            total_files_processed = 0
            for defs_path in defs_directories:
                # Calcular ruta relativa para mantener estructura (ej. 1.5/Defs -> 1.5)
                try:
                    rel_path = defs_path.parent.relative_to(mod_path)
                except ValueError:
                    rel_path = Path(".")
                
                should_process = True
                output_rel_path = rel_path

                if target_version != "Todas":
                    if merge_versions:
                        # Si combinamos, redirigimos todo a la versión destino
                        target_path = Path(target_version) if target_version != "Base" else Path(".")
                        
                        # Lógica para reemplazar la versión origen con la destino en la ruta
                        parts = rel_path.parts
                        if str(rel_path) == ".":
                            output_rel_path = target_path
                        elif re.match(r'^\d+\.\d+$', parts[0]):
                            output_rel_path = target_path.joinpath(*parts[1:])
                        else:
                            output_rel_path = target_path / rel_path
                    else:
                        is_base = str(rel_path) == "."
                        if target_version == "Base" and not is_base: should_process = False
                        if target_version != "Base" and str(rel_path) != target_version: should_process = False
                
                if not should_process: continue

                if simplify_mods:
                    parts_out = list(output_rel_path.parts)
                    mods_idx = -1
                    for i, p in enumerate(parts_out):
                        if p.lower() == 'mods':
                            mods_idx = i
                            break
                    if mods_idx != -1 and len(parts_out) > mods_idx + 1:
                        del parts_out[mods_idx:mods_idx+2]
                        output_rel_path = Path(*parts_out) if parts_out else Path(".")

                version_label = f"Version {rel_path}" if str(rel_path) != "." else "Version Base"
                if merge_versions and target_version != "Todas" and str(rel_path) != str(output_rel_path):
                    version_label += f" -> Combinado en {output_rel_path}"

                target_base_path = output_root / output_rel_path / "DefInjected"
                
                # Ruta equivalente en el archivo para Defs
                # Intentamos construir la ruta específica espejo en el archivo
                archive_base_path = None
                if archive_lang_path:
                    archive_base_path = archive_lang_path / output_rel_path / "DefInjected"
                
                version_files_log = []
                
                for root, _, files in os.walk(str(defs_path)):
                    for file in files:
                        if file.endswith('.xml'):
                            file_path = os.path.join(root, file)
                            results = self.process_file(file_path, file, target_base_path, archive_base_path)
                            version_files_log.extend(results)
                
                if version_files_log:
                    self.log(f"\n{version_label}")
                    for line in version_files_log:
                        self.log(f"   └── {line}")
                    total_files_processed += len(version_files_log)

            # --- 2. Procesar KEYED ---
            keyed_directories = []
            for root, dirs, files in os.walk(mod_path):
                if os.path.basename(root).lower() == 'keyed':
                    if 'english' in os.path.basename(os.path.dirname(root)).lower():
                        keyed_directories.append(Path(root))
            
            keyed_files_log = []
            for keyed_path in keyed_directories:
                # Calcular ruta relativa (ej. 1.5/Languages/English/Keyed -> 1.5)
                try:
                    rel_path = keyed_path.parent.parent.parent.relative_to(mod_path)
                except ValueError:
                    rel_path = Path(".")

                should_process = True
                output_rel_path = rel_path

                if target_version != "Todas":
                    if merge_versions:
                        target_path = Path(target_version) if target_version != "Base" else Path(".")
                        parts = rel_path.parts
                        if str(rel_path) == ".":
                            output_rel_path = target_path
                        elif re.match(r'^\d+\.\d+$', parts[0]):
                            output_rel_path = target_path.joinpath(*parts[1:])
                        else:
                            output_rel_path = target_path / rel_path
                    else:
                        is_base = str(rel_path) == "."
                        if target_version == "Base" and not is_base: should_process = False
                        if target_version != "Base" and str(rel_path) != target_version: should_process = False
                
                if not should_process: continue

                if simplify_mods:
                    parts_out = list(output_rel_path.parts)
                    mods_idx = -1
                    for i, p in enumerate(parts_out):
                        if p.lower() == 'mods':
                            mods_idx = i
                            break
                    if mods_idx != -1 and len(parts_out) > mods_idx + 1:
                        del parts_out[mods_idx:mods_idx+2]
                        output_rel_path = Path(*parts_out) if parts_out else Path(".")

                target_keyed_path = output_root / output_rel_path / "Keyed"
                
                # Ruta equivalente en el archivo para Keyed
                # Intentamos construir la ruta específica espejo en el archivo
                archive_keyed_path = None
                if archive_lang_path:
                    archive_keyed_path = archive_lang_path / output_rel_path / "Keyed"
                
                for root, _, files in os.walk(str(keyed_path)):
                    for file in files:
                        if file.endswith('.xml'):
                            file_path = os.path.join(root, file)
                            results = self.process_keyed_file(file_path, file, target_keyed_path, archive_keyed_path)
                            keyed_files_log.extend(results)
            
            if keyed_files_log:
                self.log(f"\nTextos Keyed (General)")
                for line in keyed_files_log:
                    self.log(f"   └── {line}")
                total_files_processed += len(keyed_files_log)
            
            self.log("\n------------------------------------------------------------")
            self.log(f"Proceso completado! Archivos procesados: {total_files_processed}")
            
            if total_files_processed == 0:
                QMessageBox.warning(self, "Aviso", "No se encontraron archivos Defs ni Keyed (en inglés).")
            else:
                if self.act_readme.isChecked():
                    self.create_readme(output_root)
                
                if self.act_create_about.isChecked():
                    self.create_minimal_about(mod_path, output_root.parent)
                
                if self.act_popup.isChecked():
                    QMessageBox.information(self, "Éxito", f"Traducciones generadas en:\n{output_root}")
        except Exception as e:
            self.log(f"ERROR CRÍTICO: {str(e)}")
            QMessageBox.critical(self, "Error", f"Ocurrió un error: {e}")

    def process_file(self, file_path, file_name, target_base_path, archive_base_path=None):
        try:
            tree = ET.parse(file_path)
            xml_root = tree.getroot()
        except ET.ParseError:
            self.log(f"Error al parsear: {file_name}")
            return []

        translations_by_type = {}

        for def_node in xml_root:
            if not isinstance(def_node.tag, str): continue
            
            def_type = def_node.tag
            def_name_node = def_node.find('defName')
            
            if def_name_node is None: continue
            
            def_name = def_name_node.text
            if not def_name: continue
            
            if def_type not in translations_by_type:
                translations_by_type[def_type] = []

            # Iniciar búsqueda recursiva dentro del Def
            self.extract_recursive(def_node, def_name, translations_by_type[def_type])

        if translations_by_type:
            return self.save_translations(translations_by_type, file_name, target_base_path, archive_base_path)
        return []

    def extract_recursive(self, node, current_path, results):
        # Helper para obtener el nombre base de un nodo lista
        def get_li_name(element):
            # 1. Intentar usar customLabel (prioridad para BodyParts)
            custom_label = element.find('customLabel')
            if custom_label is not None and custom_label.text:
                text = custom_label.text.strip()
                # Sanitizar: espacios a guiones bajos, mantener solo caracteres seguros
                text = text.replace(' ', '_')
                return "".join(c for c in text if c.isalnum() or c in ('_', '-'))
            
            # 2. Intentar usar def
            def_node = element.find('def')
            if def_node is not None and def_node.text:
                return def_node.text.strip()
            return None

        # Pre-calcular conteos para manejar duplicados
        name_counts = {}
        li_children_names = []
        
        for child in node:
            if child.tag == 'li':
                name = get_li_name(child)
                if name:
                    name_counts[name] = name_counts.get(name, 0) + 1
                li_children_names.append(name)
            else:
                li_children_names.append(None)

        name_indices = {}
        li_index = 0
        
        for i, child in enumerate(node):
            tag = child.tag
            if not isinstance(tag, str) or tag == 'defName':
                continue
            
            part = ""
            if tag == 'li':
                name = li_children_names[i]
                if name:
                    # Si hay duplicados, usar sufijo numérico
                    if name_counts.get(name, 0) > 1:
                        idx = name_indices.get(name, 0)
                        part = f"{name}-{idx}"
                        name_indices[name] = idx + 1
                    else:
                        part = name
                else:
                    # Usar índice numérico si no hay nombre
                    part = str(li_index)
                li_index += 1
            else:
                part = tag
            
            new_path = f"{current_path}.{part}"
            
            # Detectar si estamos dentro de una lista de reglas (rulesStrings)
            is_rules_list = (node.tag == 'rulesStrings' and tag == 'li')
            
            # Si es un nodo final con texto, verificar si es traducible
            if child.text and child.text.strip() and len(child) == 0:
                # Verificar blacklist
                if any(b.lower() in tag.lower() for b in self.blacklisted_tags):
                    pass
                # Si el tag está en nuestra lista blanca o es un índice de una lista traducible
                elif any(t.lower() in tag.lower() for t in self.translatable_tags) or is_rules_list:
                    results.append({'key': new_path, 'value': child.text.strip()})
            
            # Continuar buscando en profundidad
            self.extract_recursive(child, new_path, results)

    def process_keyed_file(self, file_path, file_name, target_dir, archive_dir=None):
        try:
            tree = ET.parse(file_path)
            root = tree.getroot()
        except ET.ParseError:
            self.log(f"Error al parsear Keyed: {file_name}")
            return []

        entries = []
        for child in root:
            # Ignorar comentarios o nodos sin texto
            if child.text:
                entries.append({'key': child.tag, 'value': child.text.strip()})
        
        if entries:
            return self.save_keyed_translations(entries, file_name, target_dir, archive_dir)
        return []

    def save_keyed_translations(self, entries, original_filename, target_dir, archive_dir=None):
        target_dir.mkdir(parents=True, exist_ok=True)
        output_file = target_dir / original_filename

        existing_translations = {}
        if output_file.exists():
            try:
                tree = ET.parse(output_file)
                root = tree.getroot()
                for child in root:
                    if child.tag and child.text:
                        existing_translations[child.tag] = child.text
            except ET.ParseError:
                pass
        
        # Usar la caché global cargada al inicio
        archive_translations = self.global_archive_translations

        # Intentar cargar traducciones locales específicas (prioridad alta)
        local_translations = {}
        if archive_dir:
            local_file = archive_dir / original_filename
            if local_file.exists():
                local_translations = self.load_single_xml_translations(local_file)

        with open(output_file, 'w', encoding='utf-8') as f:
            f.write('<?xml version="1.0" encoding="UTF-8"?>\n')
            f.write('<LanguageData>\n')
            
            used_keys = set()
            for entry in entries:
                used_keys.add(entry['key'])
                original_text = entry['value'].replace('--', '- -')
                val_to_write = existing_translations.get(entry['key'], "TODO")
                
                # Si es TODO, intentar recuperar del archivo (Local > Global)
                if (val_to_write == "TODO" or val_to_write == "") and entry['key'] in archive_translations:
                    if entry['key'] in local_translations:
                        val_to_write = local_translations[entry['key']]
                    else:
                        val_to_write = archive_translations[entry['key']]
                
                val_to_write = escape(val_to_write)
                
                f.write(f'\n  <!-- EN: {original_text} -->\n')
                f.write(f'  <{entry["key"]}>{val_to_write}</{entry["key"]}>\n')
            
            # Preservar traducciones antiguas (INUTILIZADO)
            unused_keys = [k for k in existing_translations if k not in used_keys]
            if unused_keys:
                f.write('\n  <!-- INUTILIZADO -->\n')
                for k in unused_keys:
                    val = existing_translations[k]
                    f.write(f'  <!-- <{k}>{val}</{k}> -->\n')

            f.write('\n</LanguageData>\n')
        
        action = "Actualizado" if existing_translations else "Generado"
        return [f"[{action}] {original_filename}"]

    def create_readme(self, output_dir):
        try:
            readme_file = output_dir / "LEEME_INSTALACION.txt"
            with open(readme_file, 'w', encoding='utf-8') as f:
                f.write("=== CÓMO INSTALAR ESTA TRADUCCIÓN ===\n\n")
                f.write("1. Ve a la carpeta del mod original.\n")
                f.write("2. Entra en la carpeta 'Languages' (créala si no existe).\n")
                f.write(f"3. Dentro, crea una carpeta llamada '{self.lang_input.text()}'.\n")
                f.write("4. COPIA todo el contenido de esta carpeta (las carpetas 1.5, DefInjected, etc.) y pégalo ahí.\n")
            self.log("Generado: LEEME_INSTALACION.txt con instrucciones.")
        except Exception:
            pass

    def create_minimal_about(self, mod_path, output_base_dir):
        try:
            # Buscar About.xml original
            source_about = None
            for p in [mod_path / "About" / "About.xml", mod_path / "About" / "about.xml"]:
                if p.exists():
                    source_about = p
                    break
            
            if not source_about:
                self.log("Aviso: No se encontró About.xml en el mod original para extraer metadatos.")
                return

            tree = ET.parse(source_about)
            root = tree.getroot()
            
            name = root.find("name")
            author = root.find("author")
            packageId = root.find("packageId")
            
            if packageId is None or not packageId.text:
                self.log("Aviso: El About.xml original no tiene packageId válido.")
                return

            # Intentar obtener PublishedFileId
            published_file_id = None
            for p in [mod_path / "PublishedFileId.txt", mod_path / "About" / "PublishedFileId.txt"]:
                if p.exists():
                    try:
                        with open(p, 'r', encoding='utf-8') as f:
                            content = f.read().strip()
                            if content:
                                published_file_id = content
                    except:
                        pass
                    if published_file_id: break

            # Crear contenido XML manualmente para controlar el formato
            about_content = [
                "<ModMetaData>",
                f"\t<name>{escape(name.text if name is not None and name.text else mod_path.name)}</name>",
                f"\t<author>{escape(author.text if author is not None and author.text else 'Unknown')}</author>",
                f"\t<packageId>{escape(packageId.text)}</packageId>"
            ]
            
            if published_file_id:
                about_content.append(f"\t<!-- PublishedFileId: {published_file_id} -->")
            
            about_content.append("</ModMetaData>")
            
            about_dir = output_base_dir / "About"
            about_dir.mkdir(parents=True, exist_ok=True)
            
            filename = f"About_{published_file_id}.xml" if published_file_id else "About.xml"
            target_file = about_dir / filename
            
            with open(target_file, 'w', encoding='utf-8') as f:
                f.write("\n".join(about_content))
                
            self.log(f"Generado: About/{filename} con packageId '{packageId.text}'")
            
            # Copiar PublishedFileId.txt si existe (útil para referencias de Steam)
            if published_file_id:
                # Ya lo leímos, pero lo copiamos igual por si acaso se necesita el txt
                for p in [mod_path / "PublishedFileId.txt", mod_path / "About" / "PublishedFileId.txt"]:
                    if p.exists():
                        shutil.copy2(p, about_dir / "PublishedFileId.txt")
                        self.log("Copiado: PublishedFileId.txt")
                        break
            
        except Exception as e:
            self.log(f"Error creando About.xml: {e}")

    def save_translations(self, translations_dict, original_filename, target_base_path, archive_base_path=None):
        # Usar la caché global cargada al inicio
        archive_translations = self.global_archive_translations
        results_log = []

        for def_type, entries in translations_dict.items():
            if not entries: continue

            # Cargar traducciones locales específicas para este DefType/Archivo (Prioridad Alta)
            local_translations = {}
            if archive_base_path:
                local_file = archive_base_path / def_type / original_filename
                if local_file.exists():
                    local_translations = self.load_single_xml_translations(local_file)

            # --- RECUPERAR CLAVES EXTRA (OPCIONAL) ---
            if self.act_recover_implicit.isChecked():
                present_defs = set()
                present_keys = set()
                for entry in entries:
                    key = entry['key']
                    present_keys.add(key)
                    if '.' in key:
                        present_defs.add(key.split('.')[0])
                    else:
                        present_defs.add(key)
                
                # Buscar en el archivo claves que pertenezcan a estos Defs
                extra_entries = []
                for arch_key, arch_val in archive_translations.items():
                    if '.' in arch_key:
                        def_part = arch_key.split('.')[0]
                        if def_part in present_defs and arch_key not in present_keys:
                            # Intentar obtener el inglés real, si no, marcar como implícito
                            english_text = self.english_translations.get(arch_key, "(Implicit/Inherited)")
                            
                            # Solo añadir si tenemos inglés O si el usuario realmente quiere forzarlo
                            # Aquí permitimos todo lo que esté en el archivo de traducción
                            extra_entries.append({
                                'key': arch_key, 
                                'value': english_text 
                            })
                entries.extend(extra_entries)
            # -----------------------------------------------------------------------

            # --- AJUSTE: Renombrar baseDesc a description y Ordenar ---
            is_backstory = 'Backstory' in def_type
            processed_entries = []
            
            for entry in entries:
                key = entry['key']
                value = entry['value']
                
                if '.' in key:
                    parts = key.split('.')
                    def_name = parts[0]
                    field = '.'.join(parts[1:])
                else:
                    def_name = key
                    field = ""

                # Si es Backstory, cambiamos baseDesc por description
                if is_backstory and field == 'baseDesc':
                    field = 'description'
                    key = f"{def_name}.{field}"
                
                processed_entries.append({'key': key, 'value': value, 'def_name': def_name, 'field': field})

            # Ordenar: label (1) -> description (2) -> title (3) -> titleShort (4) -> baseDesc (5) -> deathMessage (6) -> endMessage (7) -> otros (99)
            processed_entries.sort(key=lambda x: (x['def_name'], {'label': 1, 'description': 2, 'title': 3, 'titleShort': 4, 'baseDesc': 5, 'deathMessage': 6, 'endMessage': 7}.get(x['field'], 99)))
            
            entries = processed_entries
            # ----------------------------------------------------------

            output_dir = target_base_path / def_type
            output_dir.mkdir(parents=True, exist_ok=True)
            output_file = output_dir / original_filename
            
            existing_translations = {}
            if output_file.exists():
                try:
                    tree = ET.parse(output_file)
                    root = tree.getroot()
                    for child in root:
                        if child.tag and child.text:
                            existing_translations[child.tag] = child.text.strip()
                except Exception as e:
                    self.log(f"Advertencia: Error leyendo archivo existente {output_file.name}: {e}")

            # Escribir manualmente para incluir comentarios y formato TODO
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write('<?xml version="1.0" encoding="UTF-8"?>\n')
                f.write('<LanguageData>\n')
                f.write('  \n')
                
                last_def = None
                used_keys = set()
                for entry in entries:
                    key = entry['key']
                    used_keys.add(key)
                    current_def = key.split('.')[0] if '.' in key else key
                    
                    if last_def and current_def != last_def:
                        f.write('\n')

                    original_text = entry['value'].replace('--', '- -') # Evitar romper comentarios XML
                    
                    val_to_write = existing_translations.get(key, "TODO")
                    
                    # Si es TODO, intentar recuperar del archivo
                    if val_to_write == "TODO" or val_to_write == "":
                        # 1. Prioridad: Archivo específico en la misma ruta
                        if key in local_translations:
                            val_to_write = local_translations[key]
                        # 2. Fallback: Búsqueda global
                        elif key in archive_translations:
                            val_to_write = archive_translations[key]
                        # Fallback para Backstories (baseDesc <-> description) y otros cambios comunes
                        elif key.endswith('.baseDesc') and (key.replace('.baseDesc', '.description') in archive_translations):
                            val_to_write = archive_translations[key.replace('.baseDesc', '.description')]
                        elif key.endswith('.description') and (key.replace('.description', '.baseDesc') in archive_translations):
                            val_to_write = archive_translations[key.replace('.description', '.baseDesc')]
                        # Fallback para title <-> label
                        elif key.endswith('.title') and (key.replace('.title', '.label') in archive_translations):
                            val_to_write = archive_translations[key.replace('.title', '.label')]
                        elif key.endswith('.label') and (key.replace('.label', '.title') in archive_translations):
                            val_to_write = archive_translations[key.replace('.label', '.title')]
                        
                    val_to_write = escape(val_to_write)

                    f.write(f'  <!-- EN: {original_text} -->\n')
                    f.write(f'  <{key}>{val_to_write}</{key}>\n')
                    
                    last_def = current_def
                
                # Preservar traducciones antiguas (INUTILIZADO)
                unused_keys = [k for k in existing_translations if k not in used_keys]
                if unused_keys:
                    f.write('\n  <!-- INUTILIZADO -->\n')
                    for k in unused_keys:
                        val = existing_translations[k]
                        f.write(f'  <!-- <{k}>{val}</{k}> -->\n')
                
                f.write('  \n')
                f.write('</LanguageData>')
            
            action = "Actualizado" if existing_translations else "Generado"
            results_log.append(f"[{action}] {def_type}/{original_filename}")
        return results_log

if __name__ == "__main__":
    app = QApplication(sys.argv)
    gui = RimWorldTranslatorGUI()
    gui.show()
    sys.exit(app.exec())