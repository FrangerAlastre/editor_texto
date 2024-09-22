import os
import sys
import re

from PyQt6.QtCore import Qt, QDir, QModelIndex, QRect, QSize # Se añadieron QRect y QSize
from PyQt6.QtGui import QAction, QFont, QColor, QPalette, QSyntaxHighlighter, QTextCharFormat, QTextCursor, QFileSystemModel, QPainter, QTextFormat # Se añadieron QPainter y QTextFormat
from PyQt6.QtWidgets import (QApplication, QMainWindow, QPlainTextEdit, QFileDialog, 
                             QTreeView, QSplitter, QVBoxLayout, QWidget, QMenuBar, QTextEdit)

class PythonHighlighter(QSyntaxHighlighter):
    def __init__(self, document):
        super().__init__(document)
        self.highlighting_rules = []

        # NUEVO: Definir los formatos de texto (colores y estilos)
        self.keyword_format = QTextCharFormat()
        self.keyword_format.setForeground(QColor("#ff79c6"))  # Color para las palabras clave
        self.keyword_format.setFontWeight(QFont.Weight.Bold)

        self.string_format = QTextCharFormat()
        self.string_format.setForeground(QColor("#f1fa8c"))  # Color para las cadenas de texto

        self.comment_format = QTextCharFormat()
        self.comment_format.setForeground(QColor("#6272a4"))  # Color para los comentarios
        self.comment_format.setFontItalic(True)

        # NUEVO: Añadir las reglas de resaltado
        keywords = [
            r'\bclass\b', r'\bdef\b', r'\breturn\b', r'\bif\b', r'\belse\b', r'\belif\b',
            r'\bwhile\b', r'\bfor\b', r'\bin\b', r'\bimport\b', r'\bfrom\b', r'\bas\b', 
            r'\bwith\b', r'\btry\b', r'\bexcept\b', r'\bfinally\b', r'\bpass\b',
            r'\bcontinue\b', r'\bbreak\b', r'\braise\b', r'\bTrue\b', r'\bFalse\b', r'\bNone\b'
        ]
        # Añadir palabras clave a las reglas
        for keyword in keywords:
            pattern = re.compile(keyword)
            self.highlighting_rules.append((pattern, self.keyword_format))

        # Cadenas de texto (simples y dobles comillas)
        string_pattern = re.compile(r'\".*?\"|\'[^\']*\'')
        self.highlighting_rules.append((string_pattern, self.string_format))

        # Comentarios (empiezan con '#')
        comment_pattern = re.compile(r'#.*')
        self.highlighting_rules.append((comment_pattern, self.comment_format))

    def highlightBlock(self, text):
        """ Aplica el formato a cada bloque de texto"""
        for pattern, text_format in self.highlighting_rules:
            for match in re.finditer(pattern, text):
                start, end = match.span()
                self.setFormat(start, end - start, text_format)

        # Marcar si estamos dentro de una cadena multilínea
        in_multiline = self.match_multiline_string(text, re.compile(r'\"\"\".*?\"\"\"|\'\'\'.*?\'\'\''), self.string_format)

        # Si no estamos dentro de una cadena multilínea, resetear el estado del bloque
        if not in_multiline:
            self.setCurrentBlockState(0)

    def match_multiline_string(self, text, pattern, text_format):
        """ Verifica si el bloque contiene una cadena multilínea """
        # Si venimos de un bloque anterior que ya está en una cadena multilínea
        if self.previousBlockState() == 1:
            start_index = 0
        else:
            # Buscar el inicio de una cadena multilínea
            match = re.search(pattern, text)
            start_index = match.start() if match else -1

        while start_index >= 0:
            # Buscar el final de la cadena multilínea en el mismo bloque
            match = re.search(pattern, text[start_index:])
            if match:
                end_index = start_index + match.end()
                self.setFormat(start_index, end_index - start_index, text_format)
                start_index = re.search(pattern, text[end_index:])
                if start_index:
                    start_index = start_index.start()  # Asegurarse de obtener el índice de inicio de la próxima coincidencia
                else:
                    start_index = -1  # Si no se encuentra otro patrón, terminar el ciclo
            else:
                # No encontramos el final, entonces se trata de una cadena multilínea
                self.setFormat(start_index, len(text) - start_index, text_format)
                self.setCurrentBlockState(1)  # Estado 1: dentro de cadena multilínea
                return True

        return False

class LineNumberArea(QWidget): # Se le añadieron sus funciones
    def __init__(self, editor):
        super().__init__(editor)
        self.code_editor = editor

    def sizeHint(self):  # NUEVO
        # Ajusta el tamaño del área de número de líneas según el ancho necesario
        return QSize(self.code_editor.line_number_area_width(), 0)

    def paintEvent(self, event):  # NUEVO
        # Dibuja los números de línea
        self.code_editor.line_number_area_paint_event(event)

class CodeEditor(QPlainTextEdit):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.line_number_area = LineNumberArea(self)

        self.blockCountChanged.connect(self.update_line_number_area_width)
        self.updateRequest.connect(self.update_line_number_area)
        self.cursorPositionChanged.connect(self.highlight_current_line)

        self.update_line_number_area_width(0)
        self.highlight_current_line()

    def update_line_number_area_width(self, _=None):
        # Implementación del método
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

    def line_number_area_paint_event(self, event):  # NUEVO: Dibuja los números de línea correspondientes a los bloques visibles
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

class EditorTexto(QMainWindow):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.splitter = QSplitter(Qt.Orientation.Horizontal)

        self.tree = QTreeView()
        self.model = QFileSystemModel()
        self.model.setRootPath(QDir.rootPath())
        self.tree.setModel(self.model)
        self.tree.setRootIndex(self.model.index(QDir.currentPath()))
        self.tree.clicked.connect(self.on_file_selected)

        self.editor = CodeEditor()
        self.highlighter = PythonHighlighter(self.editor.document())
        self.setup_editor()

        self.splitter.addWidget(self.tree)
        self.splitter.addWidget(self.editor)
        self.splitter.setStretchFactor(1, 4)

        main_layout = QVBoxLayout()
        main_layout.addWidget(self.splitter)

        central_widget = QWidget()
        central_widget.setLayout(main_layout)
        self.setCentralWidget(central_widget)

        self.crearAcciones() # Cambiado para incluir la opción de abrir carpetas
        self.crearMenus()

        self.setGeometry(100, 100, 1200, 800)
        self.setWindowTitle('Editor de Código')
        self.set_dark_theme()
        self.show()

    def setup_editor(self):
        font = QFont()
        font.setFamily('Courier')
        font.setFixedPitch(True)
        font.setPointSize(10)
        self.editor.setFont(font)

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

        self.abrir_carpeta = QAction('Abrir carpeta', self)  # NUEVO
        self.abrir_carpeta.setShortcut('Ctrl+Shift+O')  # NUEVO
        self.abrir_carpeta.triggered.connect(self.abrirCarpeta)  # NUEVO

        self.salir = QAction('Salir', self)
        self.salir.setShortcut('Ctrl+Q')
        self.salir.triggered.connect(self.close)

    def crearMenus(self):
        menubar = self.menuBar()
        menu_archivo = menubar.addMenu('Archivo')
        menu_archivo.addAction(self.abrir_archivo)
        menu_archivo.addAction(self.abrir_carpeta)  # NUEVO
        menu_archivo.addAction(self.guardar_archivo)
        menu_archivo.addAction(self.salir)

    def abrirArchivo(self, file_path=None):
        path, _ = QFileDialog.getOpenFileName(self, "Abrir archivo", "", 
                                              "Archivos de texto (*.txt);;Archivos Python (*.py);;Todos los archivos (*)")
        if path:
            
            with open(path, 'r') as file:
                content = file.read()
                self.editor.setPlainText(content)

    def abrirCarpeta(self):  # NUEVO
        folder_path = QFileDialog.getExistingDirectory(self, "Abrir carpeta", "")
        if folder_path:
            self.model.setRootPath(folder_path)
            self.tree.setRootIndex(self.model.index(folder_path))

    def guardarArchivo(self):
        path, _ = QFileDialog.getSaveFileName(self, "Guardar archivo", "", 
                                              "Archivos de texto (*.txt);;Archivos Python (*.py);;Todos los archivos (*)")
        if path:
            with open(path, 'w') as file:
                content = self.editor.toPlainText()
                file.write(content)

    def on_file_selected(self, index: QModelIndex):
        file_path = self.model.filePath(index)
        if os.path.isfile(file_path):
            with open(file_path, 'r') as file:
                content = file.read()
                self.editor.setPlainText(content)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = EditorTexto()
    sys.exit(app.exec())
