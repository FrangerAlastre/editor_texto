import re
from PyQt6.QtGui import QSyntaxHighlighter, QTextCharFormat, QColor, QFont


class PythonHighlighter(QSyntaxHighlighter):
    def __init__(self, document):
        super().__init__(document)
        self.highlighting_rules = []
        self.setup_highlighting_rules()

    def setup_highlighting_rules(self):
        # Formatos
        keyword_format = QTextCharFormat()
        keyword_format.setForeground(QColor("#ff79c6"))
        keyword_format.setFontWeight(QFont.Weight.Bold)

        string_format = QTextCharFormat()
        string_format.setForeground(QColor("#f1fa8c"))

        number_format = QTextCharFormat()
        number_format.setForeground(QColor("#bd93f9"))

        special_char_format = QTextCharFormat()
        special_char_format.setForeground(QColor("#ffb86c"))

        comment_format = QTextCharFormat()
        comment_format.setForeground(QColor("#6272a4"))
        comment_format.setFontItalic(True)

        self.multi_line_comment_format = QTextCharFormat()
        self.multi_line_comment_format.setForeground(QColor("#6272a4"))
        self.multi_line_comment_format.setFontItalic(True)

        # Palabras clave
        keywords = [
            r'\bclass\b', r'\bdef\b', r'\breturn\b', r'\bif\b', r'\belse\b', r'\belif\b',
            r'\bwhile\b', r'\bfor\b', r'\bin\b', r'\bimport\b', r'\bfrom\b', r'\bas\b',
            r'\bwith\b', r'\btry\b', r'\bexcept\b', r'\bfinally\b', r'\bpass\b',
            r'\bcontinue\b', r'\bbreak\b', r'\braise\b', r'\bTrue\b', r'\bFalse\b', r'\bNone\b'
        ]

        # Reglas de resaltado
        for keyword in keywords:
            pattern = re.compile(keyword)
            self.highlighting_rules.append((pattern, keyword_format))

        self.highlighting_rules.extend([
            (re.compile(r'\b\d+\b'), number_format),
            (re.compile(r'\".*?\"|\'.*?\''), string_format),
            (re.compile(r'#.*'), comment_format),
            (re.compile(r'[\+\-\*/=()\[\]{}:;]'), special_char_format)
        ])

    def highlightBlock(self, text):
        # Resaltar reglas estándar
        for pattern, format in self.highlighting_rules:
            for match in pattern.finditer(text):
                start, end = match.span()
                self.setFormat(start, end - start, format)

        # Resaltar comentarios multilínea
        self.setCurrentBlockState(0)

        # Resaltar comentarios multilínea que comienzan o terminan en el bloque actual
        start_index = 0
        if self.previousBlockState() != 1:
            start_index = text.find("'''")
            if start_index == -1:
                start_index = text.find('"""')

        while start_index >= 0:
            if self.previousBlockState() == 1:
                # Si estamos en un comentario iniciado previamente
                start_index = 0

            end_index = text.find("'''", start_index + 3)
            if end_index == -1:
                end_index = text.find('"""', start_index + 3)

            if end_index == -1:
                # Comentario continúa en el siguiente bloque
                self.setFormat(start_index, len(text) - start_index, self.multi_line_comment_format)
                self.setCurrentBlockState(1)
                break
            else:
                # Comentario termina en el bloque actual
                comment_length = end_index + 3 - start_index
                self.setFormat(start_index, comment_length, self.multi_line_comment_format)
                start_index = text.find("'''", end_index + 3)
                if start_index == -1:
                    start_index = text.find('"""', end_index + 3)
