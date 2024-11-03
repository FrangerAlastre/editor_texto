import os
import shutil
from PyQt6.QtGui import QAction
from PyQt6.QtCore import Qt, QDir
from PyQt6.QtGui import QIcon, QColor, QPalette, QFileSystemModel
from PyQt6.QtWidgets import (QMainWindow, QFileDialog, QSplitter, QVBoxLayout, 
                           QWidget, QLabel, QPushButton, QHBoxLayout, QLineEdit,
                           QMessageBox, QInputDialog, QTabWidget, QMenu)
from .tree_view import DragDropTreeView
from ..editor.code_editor import CodeEditor

#featurecolor

class EditorTexto(QMainWindow):
    def __init__(self):
        super().__init__()
        
        project_dir = os.path.dirname(os.path.abspath(__file__))

        # Construye la ruta relativa al logo
        logo_path = os.path.join(project_dir, 'logo', 'Designer (1).ico')

        # Configura el ícono de la ventana usando la ruta relativa
        self.setWindowIcon(QIcon(logo_path))
        self.initUI()
        self.current_file = None

    def initUI(self):

        self.welcome_screen = QWidget()
        welcome_layout = QVBoxLayout()

        self.welcome_label = QLabel("Bienvenido")
        self.welcome_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        welcome_layout.addWidget(self.welcome_label)
        self.welcome_label.setStyleSheet("""
         QLabel {
            font-family: 'Segoe UI', sans-serif;
            font-size: 48px;
            color: white;
            padding: 20px;
            border-radius: 10px;
        }
        """)
        welcome_layout.addWidget(self.welcome_label)

        self.open_workspace_btn = QPushButton("Abrir nueva área de trabajo")
        self.open_workspace_btn.clicked.connect(self.abrirCarpeta)
        welcome_layout.addWidget(self.open_workspace_btn)
        self.open_workspace_btn.setStyleSheet("""
        QPushButton {
            font-family: 'Segoe UI', sans-serif;
            font-size: 24px;
            color: white;
            background-color: #007ACC;
            padding: 10px 20px;
            border: none;
            border-radius: 5px;
        }
        QPushButton:hover {
            background-color: #005A9E;  /* Efecto hover, un poco más oscuro */
        }
       """)
        welcome_layout.addWidget(self.open_workspace_btn)

        self.welcome_screen.setLayout(welcome_layout)
        self.setCentralWidget(self.welcome_screen)

        self.crearAcciones()
        self.crearMenus()

        self.setGeometry(100, 100, 1200, 800)
        self.setWindowTitle('Editor de Código')
        self.set_dark_theme()

        self.tab_widget = QTabWidget()
        self.tab_widget.setTabsClosable(True)
        self.tab_widget.tabCloseRequested.connect(self.close_tab)

        self.show()

    def move_file(self, index):
        source_path = self.model.filePath(index)
        if not os.path.exists(source_path):
            QMessageBox.warning(self, "Error", f"El archivo {source_path} ya no existe.")
            return

        target_folder = QFileDialog.getExistingDirectory(self, "Seleccionar carpeta destino")
        if target_folder:
            try:
                file_name = os.path.basename(source_path)
                target_path = os.path.join(target_folder, file_name)
                
                # Verificar si el archivo ya existe en el destino
                if os.path.exists(target_path):
                    reply = QMessageBox.question(self, "Archivo existente",
                                                 f"El archivo {file_name} ya existe en la carpeta destino. ¿Desea reemplazarlo?",
                                                 QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
                    if reply == QMessageBox.StandardButton.No:
                        return

                shutil.move(source_path, target_path)
                self.model.setRootPath(self.model.rootPath())  # Actualizar la vista
                QMessageBox.information(self, "Éxito", f"Archivo movido exitosamente a {target_folder}")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"No se pudo mover el archivo: {str(e)}")




    def setup_workspace_ui(self):
        self.splitter = QSplitter(Qt.Orientation.Horizontal)

        self.tree = DragDropTreeView()  # Usar la nueva clase DragDropTreeView
        self.model = QFileSystemModel()
        self.tree.setModel(self.model)
        self.tree.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.tree.customContextMenuRequested.connect(self.show_context_menu)
        self.tree.clicked.connect(self.on_file_selected)

        button_layout = QHBoxLayout()
        self.btn_crear_archivo = QPushButton("new file...")
        self.btn_crear_archivo.clicked.connect(self.crearArchivo)
        button_layout.addWidget(self.btn_crear_archivo)

        self.btn_crear_carpeta = QPushButton("new folder...")
        self.btn_crear_carpeta.clicked.connect(self.crearCarpeta)
        button_layout.addWidget(self.btn_crear_carpeta)

        self.input_nombre = QLineEdit()
        self.input_nombre.setPlaceholderText("Nombre del archivo/carpeta")
        button_layout.addWidget(self.input_nombre)

        sidebar_layout = QVBoxLayout()
        sidebar_layout.addLayout(button_layout)
        sidebar_layout.addWidget(self.tree)

        sidebar_widget = QWidget()
        sidebar_widget.setLayout(sidebar_layout)

        self.splitter.addWidget(sidebar_widget)
        self.splitter.addWidget(self.tab_widget)
        self.splitter.setStretchFactor(1, 4)

        self.setCentralWidget(self.splitter)

    def show_context_menu(self, position):
        index = self.tree.indexAt(position)
        menu = QMenu()

        if index.isValid():
            if self.model.isDir(index):
                create_file_action = menu.addAction("Crear archivo")
                create_file_action.triggered.connect(lambda: self.create_file_in_folder(index))
                
                create_folder_action = menu.addAction("Crear carpeta")
                create_folder_action.triggered.connect(lambda: self.create_folder_in_folder(index))
            
            delete_action = menu.addAction("Eliminar")
            delete_action.triggered.connect(lambda: self.delete_item(index))
            
            if not self.model.isDir(index):
                move_action = menu.addAction("Mover")
                move_action.triggered.connect(lambda: self.move_file(index))

        else:
            # Si no se hizo clic en un elemento válido, asumimos que se hizo clic en el espacio vacío
            create_file_action = menu.addAction("Crear archivo ")
            create_file_action.triggered.connect(lambda: self.create_file_in_folder(self.model.index(self.model.rootPath())))
            
            create_folder_action = menu.addAction("Crear carpeta ")
            create_folder_action.triggered.connect(lambda: self.create_folder_in_folder(self.model.index(self.model.rootPath())))

        menu.exec(self.tree.viewport().mapToGlobal(position))

    def create_file_in_folder(self, index):
        folder_path = self.model.filePath(index)
        file_name, ok = QInputDialog.getText(self, "Crear archivo", "Nombre del archivo:")
        if ok and file_name:
            full_path = os.path.join(folder_path, file_name)
            try:
                with open(full_path, 'w') as file:
                    file.write("")
                self.model.setRootPath(self.model.rootPath())
            except IOError:
                QMessageBox.warning(self, "Error", f"No se pudo crear el archivo: {full_path}")

    def create_folder_in_folder(self, index):
        parent_path = self.model.filePath(index)
        folder_name, ok = QInputDialog.getText(self, "Crear carpeta", "Nombre de la carpeta:")
        if ok and folder_name:
            full_path = os.path.join(parent_path, folder_name)
            try:
                os.makedirs(full_path, exist_ok=True)
                self.model.setRootPath(self.model.rootPath())
            except OSError:
                QMessageBox.warning(self, "Error", f"No se pudo crear la carpeta: {full_path}")

    def delete_item(self, index):
        path = self.model.filePath(index)
        item_type = "carpeta" if self.model.isDir(index) else "archivo"
        reply = QMessageBox.question(self, "Confirmar eliminación",
                                     f"¿Estás seguro de que quieres eliminar este {item_type}?\n{path}",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            try:
                if self.model.isDir(index):
                    QDir(path).removeRecursively()
                else:
                    os.remove(path)
                self.model.setRootPath(self.model.rootPath())
            except OSError as e:
                QMessageBox.warning(self, "Error", f"No se pudo eliminar el {item_type}: {str(e)}")


    def set_dark_theme(self):
        palette = QPalette()
        palette.setColor(QPalette.ColorRole.Window, QColor(53, 53, 53))
        palette.setColor(QPalette.ColorRole.WindowText, Qt.GlobalColor.white)
        palette.setColor(QPalette.ColorRole.Base, QColor(25, 25, 25))
        palette.setColor(QPalette.ColorRole.AlternateBase, QColor(53, 53, 53))
        palette.setColor(QPalette.ColorRole.ToolTipBase, Qt.GlobalColor.white)
        palette.setColor(QPalette.ColorRole.ToolTipText, Qt.GlobalColor.white)
        palette.setColor(QPalette.ColorRole.Text, Qt.GlobalColor.white)
        palette.setColor(QPalette.ColorRole.Button, QColor(53, 53, 53))
        palette.setColor(QPalette.ColorRole.ButtonText, Qt.GlobalColor.white)
        palette.setColor(QPalette.ColorRole.BrightText, Qt.GlobalColor.red)
        palette.setColor(QPalette.ColorRole.Link, QColor(42, 130, 218))
        palette.setColor(QPalette.ColorRole.Highlight, QColor(42, 130, 218))
        palette.setColor(QPalette.ColorRole.HighlightedText, Qt.GlobalColor.black)
        self.setPalette(palette)

    def crearAcciones(self):
        self.abrir_archivo = QAction('Abrir', self)
        self.abrir_archivo.setShortcut('Ctrl+O')
        self.abrir_archivo.triggered.connect(self.abrirArchivo)

        self.guardar_archivo = QAction('Guardar', self)
        self.guardar_archivo.setShortcut('Ctrl+S')
        self.guardar_archivo.triggered.connect(self.guardarArchivo)

        self.abrir_carpeta = QAction('Abrir carpeta', self)
        self.abrir_carpeta.setShortcut('Ctrl+Shift+O') 
        self.abrir_carpeta.triggered.connect(self.abrirCarpeta)

        self.salir = QAction('Salir', self)
        self.salir.setShortcut('Ctrl+Q')
        self.salir.triggered.connect(self.close)

    def crearMenus(self):
        menubar = self.menuBar()
        menubar.setStyleSheet("""
            QMenuBar {
                background-color: #353535;  /* Color de fondo oscuro */
                color: white;  /* Color del texto */
            }
            QMenuBar::item:selected { 
                background-color: #505050;  /* Color de fondo para item seleccionado */
            }
            QMenuBar::item:pressed {
                background-color: #505050;  /* Color de fondo cuando el item está presionado */
            }
            QMenu {
                background-color: #353535;
                color: white;
                border: 1px solid #2c2c2c;
            }
            QMenu::item:selected {
                background-color: #505050;
                color: white;
            }
        """)
        
        menu_archivo = menubar.addMenu('Archivo')
        menu_archivo.addAction(self.abrir_archivo)
        menu_archivo.addAction(self.abrir_carpeta)
        menu_archivo.addAction(self.guardar_archivo)
        menu_archivo.addAction(self.salir)

    def crearArchivo(self):
        file_name = self.input_nombre.text().strip()
        if file_name:
            folder_path = self.model.rootPath()
            full_path = os.path.join(folder_path, file_name)
            if not full_path.endswith(('.txt', '.py')):
                full_path += '.txt'  # Asignar una extensión por defecto

            with open(full_path, 'w') as file:
                file.write("")  # Crear archivo vacío

            self.model.setRootPath(folder_path)  # Actualizar la vista del directorio
            self.input_nombre.clear()  # Limpiar el campo de entrada

    def crearCarpeta(self):
        folder_name = self.input_nombre.text().strip()
        if folder_name:
            folder_path = self.model.rootPath()
            new_folder_path = os.path.join(folder_path, folder_name)
            os.makedirs(new_folder_path, exist_ok=True)  # Crear carpeta

            self.model.setRootPath(folder_path)  # Actualizar la vista del directorio
            self.input_nombre.clear()  # Limpiar el campo de entrada

    def close_tab(self, index):
        self.tab_widget.removeTab(index)

    def on_file_selected(self, index):
        file_path = self.model.filePath(index)
        if os.path.isfile(file_path):
            self.open_file(file_path)

    def open_file(self, file_path):
    # Verificar si el archivo ya está abierto
        for i in range(self.tab_widget.count()):
            if self.tab_widget.tabToolTip(i) == file_path:
                self.tab_widget.setCurrentIndex(i)
                return

        # Si no está abierto, crear una nueva pestaña
        try:
            # Intentar abrir el archivo con utf-8
            with open(file_path, 'r', encoding='utf-8') as file:
                content = file.read()
        except UnicodeDecodeError:
            # Si utf-8 falla, intentar con latin-1
            with open(file_path, 'r', encoding='latin-1') as file:
                content = file.read()

        editor = CodeEditor()  # Usar la nueva versión de CodeEditor
        editor.setPlainText(content)

        tab_name = os.path.basename(file_path)
        index = self.tab_widget.addTab(editor, tab_name)
        self.tab_widget.setTabToolTip(index, file_path)
        self.tab_widget.setCurrentIndex(index)

    def abrirArchivo(self, file_path=None):
        if not file_path:
            file_path, _ = QFileDialog.getOpenFileName(self, "Abrir archivo", "", 
                                                  "Archivos de texto (*.txt);;Archivos Python (*.py);;Todos los archivos (*)")
        if file_path:
            self.open_file(file_path)

    def guardarArchivo(self):
        current_tab = self.tab_widget.currentWidget()
        if isinstance(current_tab, CodeEditor):
            file_path = self.tab_widget.tabToolTip(self.tab_widget.currentIndex())
            if file_path:
                with open(file_path, 'w') as file:
                    file.write(current_tab.toPlainText())
            else:
                self.guardarArchivoComo()
                

    def guardarArchivoComo(self):
        current_tab = self.tab_widget.currentWidget()
        if isinstance(current_tab, CodeEditor):
            path, _ = QFileDialog.getSaveFileName(self, "Guardar archivo como", "", 
                                                  "Archivos de texto (*.txt);;Archivos Python (*.py);;Todos los archivos (*)")
            if path:
                with open(path, 'w') as file:
                    file.write(current_tab.toPlainText())
                self.tab_widget.setTabText(self.tab_widget.currentIndex(), os.path.basename(path))
                self.tab_widget.setTabToolTip(self.tab_widget.currentIndex(), path)

    def abrirCarpeta(self):
        folder_path = QFileDialog.getExistingDirectory(self, "Abrir carpeta", "")
        if folder_path:
            if not hasattr(self, 'model'):
                self.setup_workspace_ui()
        
            self.model.setRootPath(folder_path)
            self.tree.setRootIndex(self.model.index(folder_path))
