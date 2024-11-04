from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QPlainTextEdit, QWidget,QTextEdit 
from PyQt6.QtGui import QPainter, QColor, QTextFormat , QPalette,QFont
from .syntax_highlighter import PythonHighlighter
from .line_numbers import LineNumberArea

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

        self.apply_dark_theme()
        self.set_editor_font()



    def set_editor_font(self):
        # Cambiar la fuente a una más moderna
        font = QFont("Cascadia Code", 11)  # Puedes cambiar "Fira Code" por cualquier otra fuente
        font.setStyleHint(QFont.StyleHint.Monospace)
        self.setFont(font)    



   
    def apply_dark_theme(self):
        palette = QPalette()
        palette.setColor(QPalette.ColorRole.Base, QColor(25, 25, 25))  # Fondo del editor
        palette.setColor(QPalette.ColorRole.Text, QColor(255, 255, 255))  # Texto del editor
        self.setPalette(palette)



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

