import ply.yacc as yacc
import ply.lex as lex

class Lexer:
    reserved = {
        'if': 'IF',
        'else': 'ELSE',
        'while': 'WHILE',
        'for': 'FOR',
        'def': 'DEF',
        'return': 'RETURN',
        'print': 'PRINT',
        'and': 'AND',
        'or': 'OR',
        'not': 'NOT',
        'in': 'IN'
    }

    tokens = [
        'IDENTIFIER', 'NUMBER', 'STRING', 'FLOAT',
        'PLUS', 'MINUS', 'TIMES', 'DIVIDE', 'MODULO',
        'LESS', 'GREATER', 'LESS_EQUAL', 'GREATER_EQUAL', 
        'EQUALS', 'EQUALS_EQUALS', 'NOT_EQUALS',
        'LPAREN', 'RPAREN', 'LBRACE', 'RBRACE', 
        'COLON', 'COMMA', 'INDENT', 'DEDENT','LBRACKET', 'RBRACKET'
    ] + list(reserved.values())

    # Operadores
    t_PLUS = r'\+'
    t_MINUS = r'-'
    t_TIMES = r'\*'
    t_DIVIDE = r'/'
    t_MODULO = r'%'

    # Comparadores
    t_LESS = r'<'
    t_GREATER = r'>'
    t_LESS_EQUAL = r'<='
    t_GREATER_EQUAL = r'>='
    t_EQUALS = r'='
    t_EQUALS_EQUALS = r'=='
    t_NOT_EQUALS = r'!='

    # Paréntesis y delimitadores
    t_LPAREN = r'\('
    t_RPAREN = r'\)'
    t_LBRACE = r'\{'
    t_RBRACE = r'\}'
    t_COLON = r':'
    t_COMMA = r','
    t_LBRACKET = r'\['
    t_RBRACKET = r'\]'

    # Parsing de números y cadenas
    t_NUMBER = r'\d+'
    t_FLOAT = r'\d+\.\d+'
    t_STRING = r'"[^"]*"|\'[^\']*\''

    t_ignore = ' \t'
    def t_multiline_comment(self, t):
        r"'''(.|\n)*?'''"
        t.lexer.lineno += t.value.count('\n')
        pass  # No retorna un token, simplemente lo ignora
    def t_newline(self, t):
        r'\n+'
        t.lexer.lineno += len(t.value)

    def t_IDENTIFIER(self, t):
        r'[a-zA-Z_][a-zA-Z_0-9]*'
        t.type = self.reserved.get(t.value, 'IDENTIFIER')
        return t

    def t_error(self, t):
        print(f"Error léxico: Carácter ilegal '{t.value[0]}' en la línea {t.lineno}")
        t.lexer.skip(1)

    def build(self, **kwargs):
        self.lexer = lex.lex(module=self, **kwargs)

    def input(self, data):
     self.lexer.input(data)

    def token(self):
        return self.lexer.token()

class Parser:
    def __init__(self):
        self.lexer = Lexer()
        self.lexer.build()
        self.tokens = self.lexer.tokens
        self.parser = None
        self.errors = []
        self.success = True

    def build(self, **kwargs):
        self.parser = yacc.yacc(module=self, **kwargs, debug=False, write_tables=False)

    def p_program(self, p):
        '''program : statement_list'''
        p[0] = ('PROGRAM', p[1])

    def p_statement_list(self, p):
        '''statement_list : statement
                          | statement_list statement'''
        if len(p) == 2:
            p[0] = [p[1]]
        else:
            p[0] = p[1] + [p[2]]

    def p_statement(self, p):
        '''statement : assignment
                     | if_statement
                     | while_statement
                     | for_statement
                     | function_definition
                     | function_call
                     | print_statement
                     | return_statement'''
        p[0] = p[1]

    def p_assignment(self, p):
        '''assignment : IDENTIFIER EQUALS expression'''
        p[0] = ('ASSIGN', p[1], p[3])

    def p_if_statement(self, p):
        '''if_statement : IF expression COLON statement_list
                        | IF expression COLON statement_list ELSE COLON statement_list'''
        if len(p) == 5:
            p[0] = ('IF', p[2], ('BLOCK', p[4]), None)
        else:
            p[0] = ('IF', p[2], ('BLOCK', p[4]), ('ELSE', ('BLOCK', p[7])))
    def p_expression_group(self, p):
        '''expression : LPAREN expression RPAREN'''
        p[0] = p[2]

    def p_while_statement(self, p):
        '''while_statement : WHILE expression COLON statement_list'''
        p[0] = ('WHILE', p[2], ('BLOCK', p[4]))

    def p_expression_list(self, p):
        '''expression : LBRACE argument_list RBRACE
                    | LBRACKET argument_list RBRACKET'''
        p[0] = ('LIST', p[2])

    def p_for_statement(self, p):
        '''for_statement : FOR IDENTIFIER IN expression COLON statement_list'''
        p[0] = ('FOR', p[2], p[4], ('BLOCK', p[6]))

    def p_function_definition(self, p):
        '''function_definition : DEF IDENTIFIER LPAREN parameter_list RPAREN COLON statement_list'''
        p[0] = ('FUNCTION_DEF', p[2], p[4], ('BLOCK', p[7]))
    
    def p_parameter_list(self, p):
        '''parameter_list : 
                          | IDENTIFIER
                          | parameter_list COMMA IDENTIFIER'''
        if len(p) == 1:
            p[0] = []
        elif len(p) == 2:
            p[0] = [p[1]]
        else:
            p[0] = p[1] + [p[3]]

    def p_function_call(self, p):
        '''function_call : IDENTIFIER LPAREN argument_list RPAREN'''
        p[0] = ('FUNCTION_CALL', p[1], p[3])

    def p_argument_list(self, p):
        '''argument_list : 
                         | expression
                         | argument_list COMMA expression'''
        if len(p) == 1:
            p[0] = []
        elif len(p) == 2:
            p[0] = [p[1]]
        else:
            p[0] = p[1] + [p[3]]

    def p_print_statement(self, p):
        '''print_statement : PRINT LPAREN expression RPAREN'''
        p[0] = ('PRINT', p[3])

    def p_return_statement(self, p):
        '''return_statement : RETURN expression'''
        p[0] = ('RETURN', p[2])

    def p_expression(self, p):
        '''expression : expression PLUS expression
                      | expression MINUS expression
                      | expression TIMES expression
                      | expression DIVIDE expression
                      | expression LESS expression
                      | expression GREATER expression
                      | expression LESS_EQUAL expression
                      | expression GREATER_EQUAL expression
                      | expression EQUALS_EQUALS expression
                      | expression NOT_EQUALS expression
                      | IDENTIFIER
                      | NUMBER
                      | FLOAT
                      | STRING
                      | function_call'''

        if len(p) == 4:
            p[0] = ('BINARY_OP', p[2], p[1], p[3])
        else:
            p[0] = ('VALUE', p[1])

    def p_error(self, p):
        if p is None:
            error_msg = "Error sintáctico: fin inesperado de archivo"
        else:
            error_msg = f"Error sintáctico: token inesperado '{p.value}' en la línea {p.lineno}"
        
        self.errors.append(error_msg)
        self.success = False
        print(error_msg)

    def parse(self, code):
        self.errors = []
        self.success = True
    
        if not self.parser:
            self.build()

        try:
            ast = self.parser.parse(code, lexer=self.lexer.lexer)
            return self.success, self.errors, ast
        
        except Exception as e:
            self.errors.append(f"Error durante el análisis: {str(e)}")
            return False, self.errors, None

def print_ast(node, level=0):
    indent = "  " * level
    if isinstance(node, tuple):
        print(f"{indent}{node[0]}")
        for child in node[1:]:
            print_ast(child, level + 1)
    elif isinstance(node, list):
        for item in node:
            print_ast(item, level)
    else:
       print(f"{indent}{node}")