from enum import Enum, auto

class TokenType(Enum):
    IDENTIFIER = auto()   # Variables, nombres de funciones, etc.
    NUMBER = auto()       # Números (enteros o decimales)
    STRING = auto()       # Cadenas de texto
    OPERATOR = auto()     # Operadores (+, -, *, /, =, etc.)
    KEYWORD = auto()      # Palabras clave (if, else, while, for, etc.)
    DELIMITER = auto()    # Delimitadores (paréntesis, comas, dos puntos, etc.)
    COMMENT = auto()      # Comentarios
    INVALID = auto()      # Tokens inválidos

class Token:
    def __init__(self, token_type, value, line, column):
        self.type = token_type
        self.value = value
        self.line = line
        self.column = column

    def __repr__(self):
        return f'Token(type={self.type}, value={self.value}, line={self.line}, column={self.column})'

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
            '+': TokenType.OPERATOR, '-': TokenType.OPERATOR, 
            '*': TokenType.OPERATOR, '/': TokenType.OPERATOR,
            '//': TokenType.OPERATOR, '%': TokenType.OPERATOR, 
            '**': TokenType.OPERATOR, '=': TokenType.OPERATOR, 
            '+=': TokenType.OPERATOR, '-=': TokenType.OPERATOR, 
            '*=': TokenType.OPERATOR, '/=': TokenType.OPERATOR,
            '//=': TokenType.OPERATOR, '%=': TokenType.OPERATOR, 
            '**=': TokenType.OPERATOR, '==': TokenType.OPERATOR, 
            '!=': TokenType.OPERATOR, '>': TokenType.OPERATOR, 
            '<': TokenType.OPERATOR, '>=': TokenType.OPERATOR, 
            '<=': TokenType.OPERATOR
        }
        
        self.delimiters = {
            '(', ')', '[', ']', '{', '}', ',', ':', '.', ';', '@', '=', '->'
        }

    def analyze(self, code):
        tokens = []
        total_numbers = 0
        total_special_chars = 0
        total_keywords = 0
        total_invalid_chars = 0
        total_comments = 0
        total_operators = 0
        
        lines = code.split('\n')
    
        for line_num, line in enumerate(lines, 1):
            col = 0
            i = 0
            while i < len(line):
                char = line[i]

                # Ignorar espacios en blanco
                if char.isspace():
                    i += 1
                    continue
                
                # Palabras clave y identificadores
                if char.isalpha() or char == '_':
                    start = i
                    while i < len(line) and (line[i].isalnum() or line[i] == '_'):
                        i += 1
                    word = line[start:i]
                    if word in self.keywords:
                        tokens.append((TokenType.KEYWORD, word))
                        total_keywords += 1
                    else:
                        tokens.append((TokenType.IDENTIFIER, word))
                    
                # Números
                elif char.isdigit():
                    start = i
                    while i < len(line) and (line[i].isdigit() or line[i] == '.'):
                        i += 1
                    number_token = line[start:i]
                    tokens.append((TokenType.NUMBER, number_token))
                    total_numbers += len(number_token)
                    col += i - start
                
                # Strings
                elif char in '"\'':  # Strings entre comillas
                    quote = char
                    start = i
                    i += 1
                    while i < len(line) and line[i] != quote:
                        if line[i] == '\\':
                            i += 2
                        else:
                            i += 1
                    if i < len(line):
                        i += 1
                        tokens.append((TokenType.STRING, line[start:i]))
                    col += i - start
                
                # Comentarios
                elif char == '#':
                    tokens.append((TokenType.COMMENT, line[i:]))
                    total_comments += 1
                    break
                
                # Operadores y delimitadores
                elif char in self.operators or char in self.delimiters:
                    op = char
                    while i + 1 < len(line) and op + line[i + 1] in self.operators:
                        i += 1
                        op += line[i]
                    
                    if op in self.operators:
                        tokens.append((TokenType.OPERATOR, op))
                        total_operators += 1
                    elif char in self.delimiters:
                        tokens.append((TokenType.DELIMITER, char))
                    total_special_chars += len(op)
                    i += 1
                    col += len(op)

                # Caracteres no válidos
                else:
                    tokens.append((TokenType.INVALID, char))
                    total_invalid_chars += 1
                    i += 1

        return tokens, {
            'total_numbers': total_numbers,
            'total_special_chars': total_special_chars,
            'total_keywords': total_keywords,
            'total_invalid_chars': total_invalid_chars,
            'total_comments': total_comments,
            'total_operators': total_operators,
        }
