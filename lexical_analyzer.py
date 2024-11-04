from enum import Enum, auto

# Definición de TokenType usando Enum
class TokenType(Enum):
    KEYWORD = auto()
    IDENTIFIER = auto()
    NUMBER = auto()
    STRING = auto()
    OPERATOR = auto()
    DELIMITER = auto()
    COMMENT = auto()
    INVALID = auto()
    LETTER = auto()
    INDIVIDUAL_NUMBER = auto()  # Para números individuales dentro de identificadores

# Definición de la clase Token
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
        total_letters = 0
        total_numbers = 0
        total_special_chars = 0
        total_keywords = 0
        total_invalid_chars = 0
        total_comments = 0  # Contador de comentarios
        
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
                        tokens.append(Token(TokenType.KEYWORD, word, line_num, col))
                        total_keywords += 1
                    else:
                        tokens.append(Token(TokenType.IDENTIFIER, word, line_num, col))
                    
                    # Tokenizar cada letra y número del identificador o palabra clave
                    for j, w_char in enumerate(word):
                        token_type = TokenType.LETTER if w_char.isalpha() else TokenType.INDIVIDUAL_NUMBER
                        tokens.append(Token(token_type, w_char, line_num, col + j))
                        total_letters += 1 if w_char.isalpha() else 0
                        total_numbers += 1 if w_char.isdigit() else 0

                    col += i - start
                
                # Números
                elif char.isdigit():
                    start = i
                    while i < len(line) and (line[i].isdigit() or line[i] == '.'):
                        i += 1
                    number_token = line[start:i]
                    tokens.append(Token(TokenType.NUMBER, number_token, line_num, col))
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
                        tokens.append(Token(TokenType.STRING, line[start:i], line_num, col))
                    col += i - start
                
                # Comentarios
                elif char == '#':
                    tokens.append(Token(TokenType.COMMENT, line[i:], line_num, col))
                    total_comments += 1  # Contar el comentario
                    break
                
                # Operadores y delimitadores
                elif char in self.operators or char in self.delimiters:
                    op = char
                    while i + 1 < len(line) and op + line[i + 1] in self.operators:
                        i += 1
                        op += line[i]
                    
                    if op in self.operators:
                        tokens.append(Token(TokenType.OPERATOR, op, line_num, col))
                    elif char in self.delimiters:
                        tokens.append(Token(TokenType.DELIMITER, char, line_num, col))
                    total_special_chars += len(op)
                    i += 1
                    col += len(op)

                # Caracteres no válidos
                else:
                    tokens.append(Token(TokenType.INVALID, char, line_num, col))
                    total_invalid_chars += 1
                    i += 1

        return tokens, {
            'total_letters': total_letters,
            'total_numbers': total_numbers,
            'total_special_chars': total_special_chars,
            'total_keywords': total_keywords,
            'total_invalid_chars': total_invalid_chars,
            'total_comments': total_comments,
        }