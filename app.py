import os
import sys
import re
import shutil


from PyQt6.QtCore import Qt, QDir, QModelIndex, QRect, QSize
from PyQt6.QtGui import QAction, QFont, QColor, QPalette, QSyntaxHighlighter, QTextCharFormat, QTextCursor, QFileSystemModel, QPainter, QTextFormat , QDrag, QIcon
from PyQt6.QtWidgets import (QApplication, QMainWindow, QPlainTextEdit, QFileDialog, QAbstractItemView,
                             QTreeView, QSplitter, QVBoxLayout, QWidget, QMenuBar, QTextEdit,
                             QPushButton, QHBoxLayout, QLabel, QLineEdit, QDialog, QTabWidget,
                             QMenu, QInputDialog, QMessageBox)

class PythonHighlighter(QSyntaxHighlighter):
    def __init__(self, document):
        super().__init__(document)
        self.highlighting_rules = []

        # Definir formatos para diferentes tipos de tokens
        keyword_format = QTextCharFormat()
        keyword_format.setForeground(QColor("#ff79c6"))
        keyword_format.setFontWeight(QFont.Weight.Bold)

        string_format = QTextCharFormat()
        string_format.setForeground(QColor("#f1fa8c"))

        comment_format = QTextCharFormat()
        comment_format.setForeground(QColor("#6272a4"))
        comment_format.setFontItalic(True)

        # Definir palabras clave y patrones
        keywords = [
            r'\bclass\b', r'\bdef\b', r'\breturn\b', r'\bif\b', r'\belse\b', r'\belif\b',
            r'\bwhile\b', r'\bfor\b', r'\bin\b', r'\bimport\b', r'\bfrom\b', r'\bas\b', 
            r'\bwith\b', r'\btry\b', r'\bexcept\b', r'\bfinally\b', r'\bpass\b',
            r'\bcontinue\b', r'\bbreak\b', r'\braise\b', r'\bTrue\b', r'\bFalse\b', r'\bNone\b'
        ]

        # Agregar reglas de resaltado
        for keyword in keywords:
            pattern = re.compile(keyword)
            self.highlighting_rules.append((pattern, keyword_format))

        # Reglas para strings y comentarios
        self.highlighting_rules.append((re.compile(r'\".*?\"|\'.*?\''), string_format))
        self.highlighting_rules.append((re.compile(r'#.*'), comment_format))

    def highlightBlock(self, text):
        for pattern, format in self.highlighting_rules:
            for match in pattern.finditer(text):
                start, end = match.span()
                self.setFormat(start, end - start, format)

class CodeEditor(QPlainTextEdit):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.highlighter = PythonHighlighter(self.document())
        
        # Conectar la señal textChanged al método de actualización
        self.textChanged.connect(self.update_highlighting)

    def update_highlighting(self):
        # Este método se llama cada vez que el texto cambia
        # El resaltador se actualizará automáticamente
        pass

class LineNumberArea(QWidget):
    def __init__(self, editor):
        super().__init__(editor)
        self.code_editor = editor

    def sizeHint(self):
        return QSize(self.code_editor.line_number_area_width(), 0)

    def paintEvent(self, event):
        self.code_editor.line_number_area_paint_event(event)

class CodeEditor(QPlainTextEdit):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.line_number_area = LineNumberArea(self)
        
        # Agregar el resaltador de sintaxis aquí
        self.highlighter = PythonHighlighter(self.document())

        # Conectar los eventos de actualización
        self.blockCountChanged.connect(self.update_line_number_area_width)
        self.updateRequest.connect(self.update_line_number_area)
        self.cursorPositionChanged.connect(self.highlight_current_line)

        self.update_line_number_area_width(0)
        self.highlight_current_line()


    def update_line_number_area_width(self, _=None):
        self.setViewportMargins(self.line_number_area_width(), 0, 0, 0)

    def line_number_area_width(self):
        digits = 1
        max_block = max(1, self.blockCount())
        while max_block >= 10:
            max_block /= 10
            digits += 1
        space = 3 + self.fontMetrics().horizontalAdvance('9') * digits
        return space

    def resizeEvent(self, event):
        super().resizeEvent(event)
        cr = self.contentsRect()
        self.line_number_area.setGeometry(cr.left(), cr.top(), self.line_number_area_width(), cr.height())

    def update_line_number_area(self, rect, dy):
        if dy:
            self.line_number_area.scroll(0, dy)
        else:
            self.line_number_area.update(0, rect.y(), self.line_number_area.width(), rect.height())
        if rect.contains(self.viewport().rect()):
            self.update_line_number_area_width(0)

    def highlight_current_line(self):
        extra_selections = []
        if not self.isReadOnly():
            selection = QTextEdit.ExtraSelection()
            line_color = QColor(Qt.GlobalColor.yellow).lighter(160)

            selection.format.setBackground(line_color)
            selection.cursor = self.textCursor()
            selection.cursor.clearSelection()

            extra_selections.append(selection)

        self.setExtraSelections(extra_selections)

    def line_number_area_paint_event(self, event):
        painter = QPainter(self.line_number_area)
        painter.fillRect(event.rect(), Qt.GlobalColor.lightGray)

        block = self.firstVisibleBlock()
        block_number = block.blockNumber()
        top = self.blockBoundingGeometry(block).translated(self.contentOffset()).top()
        bottom = top + self.blockBoundingRect(block).height()

        while block.isValid() and top <= event.rect().bottom():
            if block.isVisible() and bottom >= event.rect().top():
                number = str(block_number + 1)
                painter.setPen(Qt.GlobalColor.black)
                painter.drawText(0, int(top), self.line_number_area.width(), self.fontMetrics().height(),
                                 Qt.AlignmentFlag.AlignRight, number)

            block = block.next()
            top = bottom
            bottom = top + self.blockBoundingRect(block).height()
            block_number += 1

class DragDropTreeView(QTreeView):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setDragEnabled(True)
        self.setAcceptDrops(True)
        self.setDragDropMode(QAbstractItemView.DragDropMode.InternalMove)
        self.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)

    def mousePressEvent(self, event):
        super().mousePressEvent(event)
        if event.button() == Qt.MouseButton.LeftButton:
            self.dragStartPosition = event.position().toPoint()  # Usar .position() en PyQt6

    def mouseMoveEvent(self, event):
        if not (event.buttons() & Qt.MouseButton.LeftButton):
            return
        if (event.position().toPoint() - self.dragStartPosition).manhattanLength() < QApplication.startDragDistance():
            return
        
        drag = QDrag(self)
        mimedata = self.model().mimeData(self.selectedIndexes())
        drag.setMimeData(mimedata)
        
        drag.exec(Qt.DropAction.MoveAction)

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls() or event.source() == self:
            event.acceptProposedAction()
        else:
            event.ignore()

    def dragMoveEvent(self, event):
        if event.mimeData().hasUrls() or event.source() == self:
            event.acceptProposedAction()
        else:
            event.ignore()

    def dropEvent(self, event):
        if event.mimeData().hasUrls():
            # Si se arrastran archivos desde fuera
            event.acceptProposedAction()
            for url in event.mimeData().urls():
                target_index = self.indexAt(event.position().toPoint())
                if target_index.isValid():
                    if self.model().isDir(target_index):
                        destination = self.model().filePath(target_index)
                    else:
                        destination = self.model().filePath(target_index.parent())
                else:
                    destination = self.model().rootPath()

                source = url.toLocalFile()
                if os.path.isfile(source):
                    shutil.move(source, os.path.join(destination, os.path.basename(source)))
                elif os.path.isdir(source):
                    shutil.move(source, destination)

            # Actualiza la vista del árbol después de mover los archivos
            self.model().setRootPath(self.model().rootPath())
        elif event.source() == self:
            # Si se arrastran archivos dentro del propio árbol (movimiento interno)
            event.acceptProposedAction()
            target_index = self.indexAt(event.position().toPoint())
            for source_index in self.selectedIndexes():
                source_path = self.model().filePath(source_index)
                if target_index.isValid():
                    if self.model().isDir(target_index):
                        destination_path = self.model().filePath(target_index)
                    else:
                        destination_path = self.model().filePath(target_index.parent())
                else:
                    destination_path = self.model().rootPath()

                # Mover archivos o carpetas internamente
                if os.path.exists(source_path):
                    shutil.move(source_path, os.path.join(destination_path, os.path.basename(source_path)))

            # Actualiza la vista del árbol después de mover los archivos
            self.model().setRootPath(self.model().rootPath())
        else:
            event.ignore()


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

if __name__ == '__main__':
    app = QApplication(sys.argv)
    project_dir = os.path.dirname(os.path.abspath(__file__))
    icon_path = os.path.join(project_dir, 'logo', 'app_icon.ico')
    app.setWindowIcon(QIcon(icon_path))
    ex = EditorTexto()
    sys.exit(app.exec())