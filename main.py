import sys
import os
from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QIcon
from editor.ui.main_window import EditorTexto

def main():
    app = QApplication(sys.argv)
    project_dir = os.path.dirname(os.path.abspath(__file__))
    icon_path = os.path.join(project_dir, 'logo', 'app_icon.ico')
    app.setWindowIcon(QIcon(icon_path))
    ex = EditorTexto()
    sys.exit(app.exec())

if __name__ == '__main__':
    main()

#franger es mrk