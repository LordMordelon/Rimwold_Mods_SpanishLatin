import sys
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                               QHBoxLayout, QLabel, QScrollArea, QFrame, QTabWidget)
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QColor, QPalette

class ColorRow(QWidget):
    """Widget personalizado para mostrar una fila de color"""
    def __init__(self, hex_code, label_text):
        super().__init__()
        
        layout = QHBoxLayout()
        layout.setContentsMargins(10, 5, 10, 5)
        
        # 1. Texto del Hex - COLOREADO
        self.hex_label = QLabel(hex_code)
        self.hex_label.setStyleSheet(f"color: {hex_code}; font-family: Consolas, monospace; font-weight: bold; font-size: 16px;")
        self.hex_label.setFixedWidth(100)
        self.hex_label.setTextInteractionFlags(Qt.TextSelectableByMouse)  # type: ignore # Permite copiar
        
        # 2. Etiqueta descriptiva - COLOREADA
        self.desc_label = QLabel(label_text)
        self.desc_label.setStyleSheet(f"color: {hex_code}; font-family: Segoe UI, sans-serif; font-size: 14px;")
        
        layout.addWidget(self.hex_label)
        layout.addWidget(self.desc_label)
        layout.addStretch() # Empuja todo a la izquierda
        
        self.setLayout(layout)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("VS Code Default Dark Mode Palette")
        self.resize(500, 600)
        
        # Datos de la paleta - Default Dark Mode de VS Code
        self.vscode_palette = [
            { "hex": "#1E1E1E", "label": "Editor Background" },
            { "hex": "#D4D4D4", "label": "Editor Foreground / Text" },
            { "hex": "#569CD6", "label": "Keywords (function, class, return)" },
            { "hex": "#9CDCFE", "label": "Variables & Properties" },
            { "hex": "#DCDCAA", "label": "Functions & Methods" },
            { "hex": "#4EC9B0", "label": "Classes & Interfaces" },
            { "hex": "#CE9178", "label": "Strings" },
            { "hex": "#B5CEA8", "label": "Numbers" },
            { "hex": "#6A9955", "label": "Comments" },
            { "hex": "#C586C0", "label": "Control Keywords (if, for, while)" }
        ]

        # Datos de la paleta - Colores adicionales de VS Code
        self.additional_colors = [
            { "hex": "#FF6B6B", "label": "Error Red" },
            { "hex": "#FFA500", "label": "Warning Orange" },
            { "hex": "#4ECDC4", "label": "Information Cyan" },
            { "hex": "#95E1D3", "label": "Success Mint" },
            { "hex": "#F38181", "label": "Light Red" },
            { "hex": "#AA96DA", "label": "Purple" },
            { "hex": "#FCB4D5", "label": "Pink" },
            { "hex": "#FFCCFF", "label": "Magenta" },
            { "hex": "#FFFFCC", "label": "Light Yellow" },
            { "hex": "#B0E0E6", "label": "Powder Blue" }
        ]

        # Configuración principal del estilo de la ventana (CSS)
        self.setStyleSheet("""
            QMainWindow { background-color: #1E1E1E; }
            QWidget { background-color: #1E1E1E; }
            QScrollArea { border: none; }
            QScrollBar:vertical {
                background: #1E1E1E;
                width: 14px;
            }
            QScrollBar::handle:vertical {
                background: #424242;
                min-height: 20px;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                background: none;
            }
        """)

        # Widget central y Scroll
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Layout principal
        main_layout = QVBoxLayout(central_widget)
        
        # Crear widget de pestañas
        tabs = QTabWidget()
        tabs.setStyleSheet("""
            QTabWidget::pane { border: 1px solid #3E3E42; }
            QTabBar::tab { background-color: #2D2D30; color: #CCCCCC; padding: 8px 20px; border: 1px solid #3E3E42; }
            QTabBar::tab:selected { background-color: #1E1E1E; color: #FFFFFF; border-bottom: 2px solid #569CD6; }
        """)
        
        # Tab 1: Default Dark Mode
        tab1 = self.create_color_tab("Default Dark Mode Colors", self.vscode_palette)
        tabs.addTab(tab1, "Default Colors")
        
        # Tab 2: Additional Colors
        tab2 = self.create_color_tab("Additional Colors", self.additional_colors)
        tabs.addTab(tab2, "More Colors")
        
        main_layout.addWidget(tabs)
        main_layout.addStretch()

    def create_color_tab(self, title_text, colors_list):
        """Crea una pestaña con la lista de colores"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Título
        title = QLabel(title_text)
        title.setStyleSheet("color: #CCCCCC; font-size: 18px; font-weight: bold; margin-bottom: 10px;")
        title.setAlignment(Qt.AlignCenter)  # type: ignore
        layout.addWidget(title)

        # Área de Scroll para la lista
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        content_widget = QWidget()
        scroll_layout = QVBoxLayout(content_widget)
        
        # Generar filas
        for item in colors_list:
            row = ColorRow(item["hex"], item["label"])
            scroll_layout.addWidget(row)
        
        scroll_layout.addStretch() # Empuja los items hacia arriba
        scroll.setWidget(content_widget)
        layout.addWidget(scroll)
        
        return widget

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())