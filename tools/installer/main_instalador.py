# main_instalador.py - Versión para instalador (usa config_instalador.py)
# allow-inline-style
import sys
import os

# ========== SOLUCIÓN PARA ERROR "lost sys.stdin" ==========
if getattr(sys, 'frozen', False):
    try:
        sys.stdin = open(os.devnull, 'r')
    except:
        pass

# Usar config del instalador
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Configuración optimizada para Windows - PyQt5
from PyQt5.QtWidgets import QApplication, QStyleFactory
from PyQt5.QtGui import QFont, QPalette, QColor
from PyQt5.QtCore import Qt, QTimer

def main():
    """Función principal para instalador"""
    print("=" * 50)
    print("CODEXIA SYSTEMS - GESTOR DE INVENTARIO v2.0")
    print("=" * 50)
    
    try:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        modules_dir = os.path.join(current_dir, 'modules')
        
        if not os.path.exists(modules_dir):
            print(f"ERROR: No se encuentra la carpeta 'modules'")
            return 1
        
        main_window_path = os.path.join(modules_dir, "main_window.py")
        if not os.path.exists(main_window_path):
            print(f"ERROR: No se encuentra main_window.py")
            return 1
        
        # Importar main_window
        sys.path.insert(0, modules_dir)
        from main_window import MainWindow
        
        # Crear aplicación
        app = QApplication(sys.argv)
        
        # Configurar High DPI para PyQt5
        try:
            app.setAttribute(Qt.AA_UseHighDpiPixmaps, True)
        except AttributeError:
            pass
        
        # Estilo Fusion
        app.setStyle(QStyleFactory.create("Fusion"))
        
        # Palette profesional
        palette = QPalette()
        palette.setColor(QPalette.Window, QColor(240, 240, 240))
        palette.setColor(QPalette.WindowText, QColor(0, 0, 0))
        palette.setColor(QPalette.Base, QColor(255, 255, 255))
        palette.setColor(QPalette.Button, QColor(240, 240, 240))
        palette.setColor(QPalette.ButtonText, QColor(0, 0, 0))
        palette.setColor(QPalette.Highlight, QColor(0, 120, 215))
        palette.setColor(QPalette.HighlightedText, QColor(255, 255, 255))
        app.setPalette(palette)
        
        # Fuente estándar
        font = QFont("Segoe UI", 9)
        app.setFont(font)
        
        # Apply central stylesheet when available; fallback to embedded CSS
        try:
            repo_root = os.path.abspath(os.path.join(current_dir, '..', '..'))
            if repo_root not in sys.path:
                sys.path.insert(0, repo_root)
            from app_core.theme import build_stylesheet
            app.setStyleSheet(build_stylesheet())
        except Exception:
            app.setStyleSheet("""
            QPushButton {
                min-height: 28px;
                padding: 4px 12px;
                font-size: 12px;
                border: 1px solid #cccccc;
                border-radius: 3px;
                background-color: #f0f0f0;
            }
            QPushButton:hover {
                background-color: #e6e6e6;
                border-color: #999999;
            }
            QLabel {
                font-size: 11px;
                color: #2c3e50;
            }
            QLineEdit, QComboBox {
                min-height: 26px;
                padding: 3px 6px;
                font-size: 12px;
                border: 1px solid #bdc3c7;
            }
            """)
        
        # Crear ventana principal
        window = MainWindow()
        window.setWindowTitle("Codexia Systems - Gestión de Inventario v2.0")
        
        # Tamaño óptimo
        window.resize(1280, 800)
        window.setMinimumSize(1024, 768)
        
        window.show()
        
        print("Aplicación instalada correctamente")
        print("=" * 50)
        
        return app.exec_()
        
    except Exception as e:
        print(f"\nERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())