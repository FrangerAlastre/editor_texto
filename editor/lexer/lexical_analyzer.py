from enum import Enum, auto

class TokenType(Enum):
    IDENTIFIER = auto()
    KEYWORD = auto()
    NUMBER = auto()
    STRING = auto()
    OPERATOR = auto()
    DELIMITER = auto()
    COMMENT = auto()
    WHITESPACE = auto()
    NEWLINE = auto()
    ERROR = auto()

class Token:
    def __init__(self, type, value, line, column):
        self.type = type
        self.value = value
        self.line = line
        self.column = column

    def __str__(self):
        return f"Token({self.type}, '{self.value}', line={self.line}, col={self.column})"

class LexicalAnalyzer:
    def __init__(self):
        self.keywords = {
            'and', 'as', 'assert', 'break', 'class', 'continue', 'def',
            'del', 'elif', 'else', 'except', 'False', 'finally', 'for',
            'from', 'global', 'if', 'import', 'in', 'is', 'lambda', 'None',
            'nonlocal', 'not', 'or', 'pass', 'raise', 'return', 'True',
            'try', 'while', 'with', 'yield'
        }
        
        self.operators = {
            '+', '-', '*', '/', '//', '%', '**', '=', '+=', '-=', '*=', '/=',
            '//=', '%=', '**=', '==', '!=', '>', '<', '>=', '<=', 'and', 'or',
            'not', 'is', 'is not', 'in', 'not in'
        }
        
        self.delimiters = {
            '(', ')', '[', ']', '{', '}', ',', ':', '.', ';', '@', '=', '->',
            '+=', '-=', '*=', '/=', '//=', '%=', '@=', '&=', '|=', '^=', '>>=',
            '<<=', '**='
        }

    def analyze(self, code):
        tokens = []
        lines = code.split('\n')
        
        for line_num, line in enumerate(lines, 1):
            col = 0
            i = 0
            while i < len(line):
                char = line[i]
                
                # Ignorar espacios en blanco
                if char.isspace():
                    i += 1
                    col += 1
                    continue
                
                # Identificadores y palabras clave
                if char.isalpha() or char == '_':
                    start = i
                    while i < len(line) and (line[i].isalnum() or line[i] == '_'):
                        i += 1
                    word = line[start:i]
                    if word in self.keywords:
                        tokens.append(Token(TokenType.KEYWORD, word, line_num, col))
                    else:
                        tokens.append(Token(TokenType.IDENTIFIER, word, line_num, col))
                    col += i - start
                
                # Números
                elif char.isdigit():
                    start = i
                    while i < len(line) and (line[i].isdigit() or line[i] == '.'):
                        i += 1
                    tokens.append(Token(TokenType.NUMBER, line[start:i], line_num, col))
                    col += i - start
                
                # Strings
                elif char in '"\'':
                    quote = char
                    start = i
                    i += 1
                    while i < len(line) and line[i] != quote:
                        if line[i] == '\\':
                            i += 2
                        else:
                            i += 1
                    i += 1
                    tokens.append(Token(TokenType.STRING, line[start:i], line_num, col))
                    col += i - start
                
                # Comentarios
                elif char == '#':
                    tokens.append(Token(TokenType.COMMENT, line[i:], line_num, col))
                    break
                
                # Operadores y delimitadores
                else:
                    # Intentar encontrar operadores de múltiples caracteres
                    op = char
                    while i + 1 < len(line) and op + line[i + 1] in self.operators:
                        i += 1
                        op += line[i]
                    
                    if op in self.operators:
                        tokens.append(Token(TokenType.OPERATOR, op, line_num, col))
                    elif char in self.delimiters:
                        tokens.append(Token(TokenType.DELIMITER, char, line_num, col))
                    else:
                        tokens.append(Token(TokenType.ERROR, char, line_num, col))
                    
                    i += 1
                    col += len(op)
            
            tokens.append(Token(TokenType.NEWLINE, '\n', line_num, len(line)))
        
        return tokens