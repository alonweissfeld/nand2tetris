import re

class CompilationEngine:
    """
    Emits a structured representation of the input source code,
    wrapped in XML tags.
    """
    def __init__(self, tokenizer):
        """
        Creates a new compilation engine with the given tokenizer.
        """
        if not tokenizer or not tokenizer.filename:
            raise TypeError('Tokenizer not valid.')

        filename = re.sub('.jack$', '1.xml', tokenizer.filename)

        self.xml = open(filename, 'w')
        self.tokenizer = tokenizer

        # Different keywords partition to digest the structure of program.
        self.class_var_dec = ['static', 'field']
        self.subroutines = ['constructor', 'function', 'method']


    def compile_class(self):
        """
        Compiles a complete class.
        """
        self.write_line('<class>')

        class_intestines = self.subroutines + self.class_var_dec
        token = None
        while token not in class_intestines and tokenizer.has_more_tokens():
            tokenizer.advance()
            type = tokenizer.current_type
            token = tokenizer.current_token
            self.write_token(token, type)

        # Reached a variable declaration or a subroutine,
        # there might be more than one.
        while token in self.class_var_dec:
            self.compile_class_var_dec()

        # Keep on writing subroutines until end of class.
        while token in self.subroutines:
            self.compile_subroutine_dec()


        self.write_line('</class>')

    def compile_class_var_dec(self):
        """
        Compiles a static variable declaration, or a field declaration.
        """
        tok = self.tokenizer
        self.write_line('<classVarDec>')

        # Iterate tokens until reaching a command break (';').
        while tok.current_token != ';':
            self.write_token(tok.current_token, tok.current_type)
            tok.advance()

        # Now write ; as part of this class variable declaration.
        self.write_token(';', 'SYMBOL')
        self.write_line('</classVarDec>')
        tok.advance()

    def compile_subroutine_dec(self):
        """
        Compiles a complete method, function, or constructor.
        """
        self.write_line('<subroutineDec>')
        self.write_lines('</subroutineDec>')

    def write_token(self, token, type):
        """
        Helper method to write a given token as an xml tag,
        defined by the given type.
        """
        # Support standart XML representation.
        token = token.replace('>', '&gt;')
        token = token.replace('<', '&lt;')
        token = token.replace('&', '&amp;')

        type = type.lower()
        line = '<{}> {} </{}>'.format(type, token, type)
        self.write_line(line)

    def write_line(self, line):
        """
        Write any given text line to the xml.
        """
        self.xml.write(line + '\n')

    def close(self):
        """
        Closes this stream.
        """
        self.xml.close()
