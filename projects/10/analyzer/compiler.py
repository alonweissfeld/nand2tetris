import re
import inspect

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

        filename = re.sub('.jack$', '.xml', tokenizer.filename)

        self.xml = open(filename, 'w')
        self.tokenizer = tokenizer

        # Different keywords and operators partition to digest
        # the structure of program.
        self.class_var_dec = ['static', 'field']
        self.subroutines = ['constructor', 'function', 'method']
        self.statements = ['let', 'do', 'if', 'while', 'return']
        self.ops = ['+', '-', '*', '/', '&', '|', '<', '>', '=']
        self.unary_ops = ['~', '-']


    def compile_class(self):
        """
        Compiles a complete class.
        """
        if not self.tokenizer.has_more_tokens():
            raise SyntaxError('No tokens available to compile.')

        self.tokenizer.advance()
        self.write_line('<class>')
        self.process('class')
        self.process(self.tokenizer.current_token) # class name
        self.process('{')

        # Reached a variable declaration or a subroutine,
        # there might be more than one.
        while self.tokenizer.current_token in self.class_var_dec:
            self.compile_class_var_dec()

        # Keep on writing subroutines until end of class.
        while self.tokenizer.current_token in self.subroutines:
            self.compile_subroutine_dec()

        self.process('}')
        self.write_line('</class>')

    def compile_class_var_dec(self):
        """
        Compiles a static variable declaration, or a field declaration.
        """
        self.write_line('<classVarDec>')

        # Iterate tokens until reaching a command break (';').
        while self.tokenizer.current_token != ';':
            self.process(self.tokenizer.current_token)

        # Now write ; as part of this class variable declaration.
        self.process(';')
        self.write_line('</classVarDec>')

    def compile_subroutine_dec(self):
        """
        Compiles a complete method, function, or constructor.
        """
        tok = self.tokenizer
        self.write_line('<subroutineDec>')

        while tok.current_token != '(':
            # E.g., constructor Square new
            self.process(self.tokenizer.current_token)

        # Write parameters list, e.g, (int Ax, int Ay, int Asize)
        self.process('(')
        self.compile_parameter_list()
        self.process(')')

        # Subroutine body
        self.compile_subroutine_body()

        # We're done with subroutine.
        self.write_line('</subroutineDec>')

    def compile_parameter_list(self):
        """
        Compiles a (possibly empty) parameter list.
        """
        self.write_line('<parameterList>')

        # Write the subroutine params.
        while self.tokenizer.current_token != ')':
            self.process(self.tokenizer.current_token)

        self.write_line('</parameterList>')

    def compile_subroutine_body(self):
        """
        Compiles a subroutine's body.
        """
        self.write_line('<subroutineBody>')
        self.process('{')

        # Before proceeding to the routine's statements,
        # check if there are any variable declarations.
        while self.tokenizer.current_token not in self.statements:
            self.compile_var_dec()

        # The subroutine body contains statements. For example,
        # let x = Ax;   let statement
        # do draw();    do statement
        # return x;     return statement
        self.compile_statements()

        self.process('}')
        self.write_line('</subroutineBody>')

    def compile_var_dec(self):
        """
        Compiles a var declaration.
        """
        self.write_line('<varDec>')
        self.process('var')

        while self.tokenizer.current_token != ';':
            self.process(self.tokenizer.current_token)

        self.process(';')
        self.write_line('</varDec>')


    def compile_statements(self):
        """
        Compiles a sequence of statements.
        """
        self.write_line('<statements>')

        # Write statements until ending closing bracket of parent subroutine.
        while self.tokenizer.current_token != '}':
            # Explicitly check statement
            statement = self.tokenizer.current_token
            if statement not in self.statements:
                s = ', '.join(self.statements)
                raise SyntaxError('Statement should start with one of ' + s)

            # Compile relevant statement.
            method = getattr(self, 'compile_' + statement)
            method()


        self.write_line('</statements>') # We're done.

    def compile_let(self):
        """
        Compiles a let statement.
        """
        self.write_line('<letStatement>')
        self.process('let')

        if self.tokenizer.current_type != 'IDENTIFIER':
            raise TypeError('Let statement must proceed with an identifier.')
        self.process(self.tokenizer.current_token)

        # Placement might be an array entring.
        if self.tokenizer.current_token == '[':
            self.compile_array_entry()

        self.process('=')
        self.compile_expression()
        self.process(';')
        self.write_line('</letStatement>')

    def compile_do(self):
        """
        Compiles a do statement.
        """
        self.write_line('<doStatement>')
        self.process('do')

        if '.' in self.tokenizer.peek():
            self.process(self.tokenizer.current_token) # Class name
            self.process(self.tokenizer.current_token) # .
            self.process(self.tokenizer.current_token) # Subroutine name
        else:
            self.process(self.tokenizer.current_token) # local routine name

        self.compile_subroutine_invoke()

        self.process(';') # end of do statement.
        self.write_line('</doStatement>')

    def compile_subroutine_invoke(self):
        """
        Compiles a subroutine invokation.
        """
        self.process('(')
        self.compile_expression_list() # Subroutine expressions list.
        self.process(')')

    def compile_if(self):
        """
        Compiles an if statement, possibly with a trailing else clause.
        """
        self.write_line('<ifStatement>')
        self.process('if')
        self.process('(')
        self.compile_expression() # E.g., x > 2
        self.process(')') # End of if condition statement.

        # if statement body
        self.process('{')
        self.compile_statements()
        self.process('}')

        # Check if there's proceeding 'else'
        if self.tokenizer.current_token == 'else':
            self.process('else')
            self.process('{')
            self.compile_statements()
            self.process('}')

        self.write_line('</ifStatement>')

    def compile_while(self):
        """
        Compiles a while statement.
        """
        self.write_line('<whileStatement>')
        self.process('while')
        self.process('(')
        self.compile_expression()
        self.process(')')

        # while's body.
        self.process('{')
        self.compile_statements()
        self.process('}')
        self.write_line('</whileStatement>')

    def compile_return(self):
        """
        Compiles a return statement.
        """
        self.write_line('<returnStatement>')
        self.process('return')

        if self.tokenizer.current_token != ';':
            self.compile_expression()

        self.process(';')
        self.write_line('</returnStatement>')

    def compile_expression(self):
        """
        Compiles an expression.
        """
        self.write_line('<expression>')

        previous_was_term = False
        while self.tokenizer.current_token not in [')', ']',';', ',']:
            if self.tokenizer.current_token in self.ops and previous_was_term:
                self.process(self.tokenizer.current_token)
            else:
                self.compile_term()
                previous_was_term = True

        self.write_line('</expression>')

    def compile_term(self):
        """
        Compiles a term. If the current token is an identifier, the routine
        must resolve it into a variable, an array entry, or a subroutine
        call. A single lookahead token, which may be [, (, or ., suffices
        to distinguish between the possibilities. Any other token is not
        part of this term and should not be advanced over.
        """
        self.write_line('<term>')

        if self.tokenizer.current_type == 'IDENTIFIER':
            # Resolve into a variable or local routine.
            self.process(self.tokenizer.current_token)

            # Resolves into array entry.
            if self.tokenizer.current_token == '[':
                self.compile_array_entry()

            # Resolves into a static soubroutine call.
            elif self.tokenizer.current_token == '.':
                self.process(self.tokenizer.current_token) # '.'
                self.process(self.tokenizer.current_token) # Subroutine name.
                self.compile_subroutine_invoke()

        elif self.tokenizer.current_token in self.unary_ops:
            self.process(self.tokenizer.current_token)
            self.compile_term()

        # Recurssive expression.
        elif self.tokenizer.current_token == '(':
            self.process(self.tokenizer.current_token)
            self.compile_expression()
            self.process(')')

        else:
            self.process(self.tokenizer.current_token)


        self.write_line('</term>')

    def compile_expression_list(self):
        """
        Compiles a (possibly empty) comma- separated list of expressions.
        """
        self.write_line('<expressionList>')

        while self.tokenizer.current_token != ')':
            self.compile_expression()

            if self.tokenizer.current_token == ')':
                break

            self.process(',') # next expression

        self.write_line('</expressionList>')

    def process(self, string):
        """
        A helper routine that handles the current token,
        and advances to get the next token.
        """
        if self.tokenizer.current_token != string:
            caller = inspect.stack()[1][3]
            msg = 'Invalid token found in {}, expected: {}'.format(caller, string)
            raise SyntaxError(msg)

        self.write_token(string, self.tokenizer.current_type)
        if self.tokenizer.has_more_tokens():
            self.tokenizer.advance()

    def compile_array_entry(self):
        """
        A helper routine to compile an array entry.
        """
        self.process('[')
        self.compile_expression()
        self.process(']')

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
