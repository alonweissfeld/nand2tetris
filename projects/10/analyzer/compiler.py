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
        self.statements = ['let', 'do', 'if', 'while', 'return']


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
        tok.advance() # Prepare for next routine.

    def compile_subroutine_dec(self):
        """
        Compiles a complete method, function, or constructor.
        """
        tok = self.tokenizer
        self.write_line('<subroutineDec>')

        while tok.current_token != '(':
            # E.g., constructor Square new
            self.write_token(tok.current_token, tok.current_type)
            tok.advance()

        # Write parameters list, e.g, (int Ax, int Ay, int Asize)
        self.write_token('(', 'SYMBOL')
        tok.advance()
        self.compile_parameter_list()

        # Deffensive - parameter list must end with parentheses.
        if tok.current_token != ')':
            raise TypeError('Parameters list must end with ")".')

        self.write_token(')', 'SYMBOL') # Donw with params list.

        # Subroutine body
        tok.advance()
        self.compile_subroutine_body()

        # We're done with subroutine.
        self.write_lines('</subroutineDec>')

    def compile_parameter_list(self):
        """
        Compiles a (possibly empty) parameter list.
        """
        tok = self.tokenizer
        self.write_line('<parameterList>')

        # Write the subroutine params.
        while tok.current_token != ')':
            self.write_token(tok.current_token, tok.current_type)
            tok.advance()

        self.write_line('</parameterList>')

    def compile_subroutine_body(self):
        """
        Compiles a subroutine's body.
        """
        tok = self.tokenizer
        self.write_line('<subroutineBody>')

        if tok.current_token != '{':
            raise TypeError('Subroutine body must start with a curly bracket.')

        self.write_token('{', 'SYMBOL')
        tok.advance()
        # The subroutine body contains statements. For example,
        # let x = Ax;   let statement
        # do draw();    do statement
        # return x;     return statement
        self.compile_statements()

        if tok.current_token != '}':
            raise TypeError('Subroutine body must end with a curely bracket.')

        self.write_token('}', 'SYMBOL')
        self.write_line('</subroutineBody>')

    def compile_statements(self):
        """
        Compiles a sequence of statements.
        """
        tok = self.tokenizer
        self.write_line('<statements>')

        # Write statements until ending closing bracket of parent subroutine.
        while tok.current_token != '}':
            statement = tok.current_token
            if statement not in self.statements:
                s = ', '.join(self.statements)
                raise TypeError('Statement should start with one of ' + s)

            # Compile relevant statement.
            method = 'compile_{}'.format(statement)
            self[method]()
            tok.advance() # Proceed to next statement

        self.write_line('</statements>') # We're done.

    def compile_let(self):
        """
        Compiles a let statement.
        """
        tok = self.tokenizer
        self.write_line('<letStatement>')

        if tok.current_token != 'let':
            raise TypeError('Let statement must start with a "let".')

        # let
        self.write_token(tok.current_token, tok.current_type)
        tok.advance()

        if tok.current_type != 'IDENTIFIER':
            raise TypeError('Let statement must proceed with an identifier.')

        # keyword (e.g., 'x')
        self.write_token(tok.current_token, tok.current_type)
        tok.advance()

        if tok.current_token != '=':
            raise TypeError('Let statement must proceed with a =.')

        # =
        self.write_token(tok.current_token, tok.current_type)
        tok.advance()

        self.compile_expression()

        if tok.current_token != ';':
            raise TypeError('Let statement must end with a ;.')

        self.write(';', 'SYMBOL')
        self.write_line('</letStatement>')

    def compile_do(self):
        """
        Compiles a do statement.
        """
        tok = self.tokenizer
        if tok.current_token != 'do':
            raise TypeError('doStatement must start with do.')

        self.write_line('<doStatement>')

        # do
        self.write_token(tok.current_token, tok.current_type)

        # Class name
        tok.advace()
        self.write_token(tok.current_token, tok.current_type)

        # .
        tok.advace()
        self.write_token(tok.current_token, tok.current_type)

        # Subroutine name
        tok.advace()
        self.write_token(tok.current_token, tok.current_type)

        # Open brackets and call to function
        tok.advance()
        self.compile_subroutine_invoke()

        tok.advance()
        if tok.current_token != ';':
            raise TypeError('doStatement must end with ;')

        self.write_tokn(';', 'SYMBOL')
        self.write_line('</doStatement>')

    def compile_subroutine_invoke(self):
        """
        Compiles a subroutine invokation.
        """
        if tok.current_token != '(':
            raise TypeError('Subroutine call must start with (')

        self.write_token(tok.current_token, tok.current_type)

        # Subroutine expressions list.
        tok.advance()
        self.compile_expression_list()

        if tok.current_token != ')':
            raise TypeError('Soubroutine call must end with )')

        self.write_token(')', 'SYMBOL') # End of subroutine call.

    def compile_if(self):
        """
        Compiles an if statement, possibly with a trailing else clause.
        """
        tok = self.tokenizer
        if tok.current_token != 'if':
            raise TypeError('ifStatement must start with if.')

        self.write_line('<ifStatement>')
        self.write_token(tok.current_token, tok.current_type) # if

        # (
        tok.advance()
        if tok.current_token != '(':
            raise TypeError('ifStatement must proceed with (.')
        self.write_tokn(tok.current_token, tok.current_type)

        # E.g., x > 2
        self.compile_expression()

        # )
        if tok.current_token != ')':
            raise TypeError('ifStatement must end with ).')
        self.write_token(tok.current_token, tok.current_type)

        # {
        tok.advance()
        if tok.current_token != '{':
            raise TypeError('ifStatement requires opening curley bracket.')
        self.write_token(tok.current_token, tok.current_type)

        self.compile_statements()

        # }
        if tok.current_token != '}':
            raise TypeError('ifStatement requires closig with curley bracket.')
        self.write_token(tok.current_token, tok.current_type)
        self.write_line('</ifStatement>')


    def compile_while(self):
        """
        Compiles a while statement.
        """
        tok = self.tokenizer
        if tok.current_token != 'while':
            raise TypeError('whileStatement must start with while.')
        self.write_line('<whileStatement>')
        self.write_token(tok.current_token, tok.current_type)

        # (
        tok.advance()
        if tok.current_token != '(':
            raise TypeError('ifStatement must proceed with (.')
        self.write_tokn(tok.current_token, tok.current_type)

        self.compile_expression()

        # )
        if tok.current_token != ')':
            raise TypeError('whileStatement must end with ).')
        self.write_token(tok.current_token, tok.current_type)

        # {
        tok.advance()
        if tok.current_token != '{':
            raise TypeError('whileStatement requires opening curley bracket.')
        self.write_token(tok.current_token, tok.current_type)

        self.compile_statements()

        # }
        if tok.current_token != '}':
            raise TypeError('whileStatement requires closig with curley bracket.')
        self.write_token(tok.current_token, tok.current_type)
        self.write_line('</whileStatement>')

    def compile_return(self):
        """
        Compiles a return statement.
        """
        tok = self.tokenizer
        if tok.current_token != 'return':
            raise TypeError('returnStatement must start with return.')
        self.write_line('<returnStatement>')
        self.write_token(tok.current_token, tok.current_type)

        tok.advance()
        if tok.current_token != ';':
            self.compile_expression()
        else:
            self.write_token(tok.current_token, tok.current_type)

        self.write_line('</returnStatement>')

    def compile_expression(self):
        """
        Compiles an expression.
        """
        tok = self.tokenizer
        self.write('<expression>')

        while tok.current_token not in [')', ';', ',']:
            tok.compile_term()
            # Todo - distinguish betwen terms and symbols?
            tok.advance()

        self.write('</expression>')

    def compile_term(self):
        """
        Compiles a term. If the current token is an identifier, the routine
        must resolve it into a variable, an array entry, or a subroutine
        call. A single lookahead token, which may be [, (, or ., suffices
        to distinguish between the possibilities. Any other token is not
        part of this term and should not be advanced over.
        """
        tok = self.tokenizer
        self.write('<term>')

        current = (tok.current_token, tok.current_type)
        if current[1] == 'IDENTIFIER':
            # Resolve into a variable, array entry or a subroutine call.
            self.write_token(current[0], current[1])

            if '.' in tok.peek():
                # Soubroutine
                tok.advance()  # '.'
                self.write_token(tok.current_token, tok.current_type)

                tok.advance() # Subroutine name.
                self.write_token(tok.current_token, tok.current_type)

                # Open brackets and call to function
                tok.advance()
                self.compile_subroutine_invoke()
        self.write('</term>')

    def compile_expression_list(self):
        """
        Compiles a (possibly empty) comma- separated list of expressions.
        """
        self.write_line('<expressionList>')

        while tok.current_token != ')':
            self.compile_expression()
            tok.advance()

        self.write_line('</expressionList>')


    def write_token(self, token, type):
        """
        Helper method to write a given token as an xml tag,
        defined by the given type.
        """
        # Support standart XML representation.
        token = token.replace('&', '&amp;')
        token = token.replace('>', '&gt;')
        token = token.replace('<', '&lt;')

        type = type.lower()
        type = type.replace('int_const', 'integerConstant')
        type = type.replace('string_const', 'stringConstant')

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
