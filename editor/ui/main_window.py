import os
import sys
import shutil
from PyQt6.QtGui import QAction
from PyQt6.QtCore import Qt, QDir
from PyQt6.QtGui import QIcon, QColor, QPalette, QFileSystemModel
from PyQt6.QtWidgets import (QMainWindow, QFileDialog, QSplitter, QVBoxLayout, QTextEdit,QDialog,QApplication,QApplication,
                           QWidget, QLabel, QPushButton, QHBoxLayout, QLineEdit,
                           QMessageBox, QInputDialog, QTabWidget, QMenu)
from .tree_view import DragDropTreeView
from ..editor.code_editor import CodeEditor
from editor.analyzer.lexical_analyzer import LexicalAnalyzer, TokenType, Token
from editor.analyzer_s.sintax_analyzer import Lexer,Parser



class EditorTexto(QMainWindow):
    def __init__(self):
        super().__init__()
        
        project_dir = os.path.dirname(os.path.abspath(__file__))

    # Construye la ruta relativa al logo
        logo_path = os.path.join(project_dir, 'logo', 'Designer (1).ico')
        
    
        # Crear el icono de la aplicación
        app_icon = QIcon(logo_path)
        

    
        # Establecer el icono de la aplicación
        self.setWindowIcon(app_icon)
        QApplication.setWindowIcon(app_icon)

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






    def lexical_analysis(self, index):
        # Obtener la ruta del archivo seleccionado
        file_path = self.model.filePath(index)

        try:
            # Leer el contenido del archivo
            with open(file_path, 'r') as file:
                code = file.read()

            if not code:
                QMessageBox.warning(self, "Advertencia", "El archivo está vacío.")
                return

            # Eliminar espacios en blanco del código
            code_without_whitespace = ''.join(code.split())

            # Instancia del analizador léxico y análisis
            analyzer = LexicalAnalyzer()
            tokens, stats = analyzer.analyze(code)  # Recibe tokens y estadísticas

            if not tokens:
                QMessageBox.warning(self, "Advertencia", "No se encontraron tokens válidos.")
                return

            # Formatear los tokens para mostrarlos en un mensaje
            token_message = "\n".join(str(token) for token in tokens)

            # Formatear estadísticas para mostrarlas
            stats_message = "\n".join(f"{key}: {value}" for key, value in stats.items())

            # Crear mensaje completo
            complete_message = (
                f"Código sin espacios:\n{code_without_whitespace}\n\n"
                f"Tokens:\n{token_message}\n\n"
                f"Estadísticas de Tokens:\n{stats_message}"
            )

            # Crear un cuadro de diálogo personalizado para mostrar los resultados
            dialog = QDialog(self)
            dialog.setWindowTitle("Resultado del Análisis Léxico")

            # Crear un QTextEdit para mostrar el mensaje completo con scroll
            text_edit = QTextEdit()
            text_edit.setPlainText(complete_message)
            text_edit.setReadOnly(True)

            # Ajustar el tamaño del cuadro de texto
            text_edit.setFixedSize(600, 400)

            # Layout para el diálogo
            layout = QVBoxLayout()
            layout.addWidget(text_edit)

            # Botón de cerrar
            close_button = QPushButton("Cerrar")
            close_button.clicked.connect(dialog.accept)
            layout.addWidget(close_button)

            dialog.setLayout(layout)

            # Ejecutar el diálogo de manera modal
            dialog.exec()

        except FileNotFoundError:
            QMessageBox.critical(self, "Error", f"El archivo {file_path} no se encontró.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudo realizar el análisis léxico: {e}", 
                             QMessageBox.StandardButton.Ok)
            

    def analyze_code(self, index):
        file_path = self.model.filePath(index)
        try:
            # Leer el contenido del archivo
            with open(file_path, 'r') as file:
                code = file.read()
            
            if not code:
                QMessageBox.warning(self, "Advertencia", "El archivo está vacío.")
                return

            # Crear una ventana de resultados
            result_dialog = QDialog(self)
            result_dialog.setWindowTitle("Resultados del Análisis")
            result_dialog.resize(800, 600)
            
            # Crear un layout vertical para la ventana
            layout = QVBoxLayout()
            
            # Crear un QTabWidget para separar análisis léxico y sintáctico
            tab_widget = QTabWidget()
            
            # Tab para análisis léxico
            lexical_tab = QWidget()
            lexical_layout = QVBoxLayout()
            lexical_text = QTextEdit()
            lexical_text.setReadOnly(True)
            lexical_layout.addWidget(lexical_text)
            lexical_tab.setLayout(lexical_layout)
            
            # Tab para análisis sintáctico
            syntactic_tab = QWidget()
            syntactic_layout = QVBoxLayout()
            syntactic_text = QTextEdit()
            syntactic_text.setReadOnly(True)
            syntactic_layout.addWidget(syntactic_text)
            syntactic_tab.setLayout(syntactic_layout)
            
            # Agregar tabs al QTabWidget
            tab_widget.addTab(lexical_tab, "Análisis Léxico")
            tab_widget.addTab(syntactic_tab, "Análisis Sintáctico")
            
            # Agregar el QTabWidget al layout principal
            layout.addWidget(tab_widget)
            
            # Botón para cerrar
            close_button = QPushButton("Cerrar")
            close_button.clicked.connect(result_dialog.close)
            layout.addWidget(close_button)
            
            result_dialog.setLayout(layout)

            # Realizar análisis léxico
            lexer = Lexer()
            lexer.build()
            lexer.input(code)
            
            # Recolectar tokens
            tokens = []
            stats = {'total_tokens': 0, 'lines': code.count('\n') + 1}
            
            while True:
                tok = lexer.token()
                if not tok:
                    break
                tokens.append(tok)
                stats['total_tokens'] += 1

            # Mostrar resultados del análisis léxico
            lexical_output = "=== Análisis Léxico ===\n\n"
            lexical_output += "Tokens encontrados:\n"
            for token in tokens:
                lexical_output += f"  Token: {token.type}, Valor: {token.value}, Línea: {token.lineno}\n"
            
            lexical_output += "\nEstadísticas del análisis léxico:\n"
            lexical_output += f"  Total de tokens: {stats['total_tokens']}\n"
            lexical_output += f"  Total de líneas: {stats['lines']}\n"
            
            lexical_text.setText(lexical_output)

            # Realizar análisis sintáctico
            parser = Parser()
            success, errors, ast = parser.parse(code)

            # Mostrar resultados del análisis sintáctico
            syntactic_output = "=== Análisis Sintáctico ===\n\n"
            
            if success:
                syntactic_output += "Análisis sintáctico exitoso!\n\n"
                syntactic_output += "Árbol Sintáctico:\n"
                
                # Función para construir la representación del árbol
                def build_ast_string(node, level=0):
                    result = ""
                    indent = "  " * level
                    if isinstance(node, tuple):
                        result += f"{indent}{node[0]}\n"
                        for child in node[1:]:
                            result += build_ast_string(child, level + 1)
                    elif isinstance(node, list):
                        for item in node:
                            result += build_ast_string(item, level)
                    else:
                        result += f"{indent}{node}\n"
                    return result
                
                syntactic_output += build_ast_string(ast)
            else:
                syntactic_output += "Errores encontrados durante el análisis sintáctico:\n"
                for error in errors:
                    syntactic_output += f"- {error}\n"
            
            syntactic_text.setText(syntactic_output)

            result_dialog.exec()

        except FileNotFoundError:
            QMessageBox.critical(self, "Error", f"El archivo {file_path} no se encontró.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error durante el análisis: {str(e)}")




    
  
        
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
                
                lexical_analysis_action = menu.addAction("Análisis Léxico")
                lexical_analysis_action.triggered.connect(lambda: self.lexical_analysis(index))

                analyze_code_action = menu.addAction("Análisis sintactico")
                analyze_code_action.triggered.connect(lambda: self.analyze_code(index))
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
        app = QApplication.instance()
        if app is None:
            app = QApplication(sys.argv)

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
        
        self.analisis_lexico = QAction('Análisis Léxico', self)
        self.analisis_lexico.setShortcut('Ctrl+L')
        self.analisis_lexico.triggered.connect(self.analizarLexico)

        self.salir = QAction('Salir', self)
        self.salir.setShortcut('Ctrl+Q')
        self.salir.triggered.connect(self.close)

    def crearMenus(self):
        menubar = self.menuBar()
        menu_archivo = menubar.addMenu('Archivo')
        menu_archivo.addAction(self.abrir_archivo)
        menu_archivo.addAction(self.abrir_carpeta)
        menu_archivo.addAction(self.guardar_archivo)
        menu_archivo.addAction(self.analisis_lexico)
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

    def analizarLexico(self):
    # Abrir un cuadro de diálogo para seleccionar un archivo
        file_path, _ = QFileDialog.getOpenFileName(
        self,
        "Seleccionar archivo para análisis léxico",
        "",
        "Python Files (*.py);;Text Files (*.txt);;All Files (*)"
        )

        if not file_path:
            QMessageBox.warning(self, "Advertencia", "No se seleccionó ningún archivo.")
            return

        try:
              
            with open(file_path, 'r') as file:
             code = file.read()
             

            # Realizar el análisis léxico
            analyzer = LexicalAnalyzer()
            tokens, stats = analyzer.analyze(code)
            code_without_whitespace = ''.join(code.split())
                # Formatear y mostrar los resultados
            self.mostrarResultados(tokens, stats, code_without_whitespace)
            
            

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error al leer o analizar el archivo: {e}")

    def mostrarResultados(self, tokens, stats,code_without_whitespace):
        # Formatear los resultados para mostrarlos en un cuadro de diálogo

        token_message = "\n".join(str(token) for token in tokens)
        stats_message = "\n".join(f"{key}: {value}" for key, value in stats.items())
        
    
        complete_message = (
            f"Código sin espacios:\n{code_without_whitespace}\n\n"
            f"Tokens:\n{token_message}\n\n"
            f"Estadísticas de Tokens:\n{stats_message}"
        )

        # Mostrar los resultados en un cuadro de diálogo
        dialog = QDialog(self)
        dialog.setWindowTitle("Resultado del Análisis Léxico")

        text_edit = QTextEdit()
        text_edit.setPlainText(complete_message)
        text_edit.setReadOnly(True)
        text_edit.setFixedSize(600, 400)

        layout = QVBoxLayout()
        layout.addWidget(text_edit)

        close_button = QPushButton("Cerrar")
        close_button.clicked.connect(dialog.accept)
        layout.addWidget(close_button)

        dialog.setLayout(layout)
        dialog.exec()        


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
