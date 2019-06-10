import re
import inspect

from writer import VMWriter
from table import SymbolTable

class CompilationEngine:
    """
    Recursive top-down compilation engine for the Jack langauge.
    Using a Tokenizer object, this module will process different
    Jack tokens and compile it to VM code using the VMWriter.
    While at it, invalid Jack syntax will raise SyntaxError.
    """
    def __init__(self, tokenizer):
        """
        Creates a new compilation engine with the given tokenizer.
        """
        if not tokenizer or not tokenizer.filename:
            raise TypeError('Tokenizer not valid.')

        filename = re.sub('.jack$', '.vm', tokenizer.filename)

        self.tokenizer = tokenizer
        self.vm_writer = VMWriter(filename)
        self.symbol_table = SymbolTable(filename)
        self.classname = self.get_classname(filename)

        self.tokenizer.seperate_all()

        # Different keywords and operators partition to digest
        # the structure of program.
        self.class_var_dec = ['static', 'field']
        self.subroutines = ['constructor', 'function', 'method']
        self.statements = ['let', 'do', 'if', 'while', 'return']
        self.ops = ['+', '-', '*', '/', '&', '|', '<', '>', '=']
        self.unary_ops = ['~', '-']

        # Determines the current subroutine in use.
        self.current_fn_type = None
        self.current_fn_name = None

        self.if_idx = 0
        self.while_idx = 0

        self.verbal_arithemtic = {
            '>': 'GT',
            '<': 'LT',
            '=': 'EQ',
            '|': 'OR',
            '-': 'SUB',
            '+': 'ADD',
            '&': 'AND'
        }

        self.verbal_unary = {
            '~': 'NOT',
            '-': 'NEG'
        }

    def compile_class(self):
        """
        Compiles a complete class.
        """
        if not self.tokenizer.has_more_tokens():
            raise SyntaxError('No tokens available to compile.')

        # Advance to the first token.
        self.tokenizer.advance()

        self.process('class')
        self.get_token() # class name
        self.process('{')

        # Reached a variable declaration or a subroutine,
        # there might be more than one.
        while self.tokenizer.current_token in self.class_var_dec:
            self.compile_class_var_dec()

        # Keep on writing subroutines until end of class.
        while self.tokenizer.current_token in self.subroutines:
            self.compile_subroutine_dec()

        # Validates the closing bracket of a class.
        self.process('}')
        self.vm_writer.close()

    def compile_class_var_dec(self):
        """
        Compiles a static variable declaration, or a field declaration.
        """
        kind = self.get_token()
        type = self.get_token()

        # Iterate tokens until reaching a command break (';').
        while self.tokenizer.current_token != ';':
            name = self.get_token()
            self.symbol_table.define(name, type, kind)

            if self.tokenizer.current_token == ',':
                self.process()

        self.process(';')

    def compile_subroutine_dec(self):
        """
        Compiles a complete method, function, or constructor.
        """
        self.current_fn_type = self.get_token() # static function, method or constructor.
        self.current_fn_return = self.get_token() # void or type.
        self.current_fn_name = self.get_token() # name of the subroutine.

        # Reset symbol table for current scope.
        self.symbol_table.start_subroutine()

        if self.current_fn_type == 'method':
            # The type of 'this' is the class name (for exmaple, 'Point').
            self.symbol_table.define('this', self.classname, 'arg')

        # Parameters list, e.g, (int Ax, int Ay, int Asize)
        self.process('(')
        self.compile_parameter_list()
        self.process(')')

        # Subroutine body
        self.compile_subroutine_body()

    def compile_parameter_list(self):
        """
        Compiles a (possibly empty) parameter list.
        """
        while self.tokenizer.current_token != ')':
            type = self.get_token()
            name = self.get_token()
            self.symbol_table.define(name, type, 'arg')

            if self.tokenizer.current_token == ',':
                self.process()

    def compile_subroutine_body(self):
        """
        Compiles a subroutine's body.
        """
        self.process('{')

        # Before proceeding to the routine's statements,
        # check if there are any variable declarations.
        while self.tokenizer.current_token not in self.statements:
            self.compile_var_dec()

        # Ouput the subroutine's declaration VM code.
        subroutine_name = '{}.{}'.format(self.classname, self.current_fn_name)
        nlocals = self.symbol_table.var_count('var')
        self.vm_writer.write_function(subroutine_name, nlocals)

        # Constructors require allocating memory to object fields.
        if self.current_fn_type == 'constructor':
            nargs = self.symbol_table.var_count('field')
            self.vm_writer.write_push('constant', nargs)
            self.vm_writer.write_call('Memory.alloc', 1)
            self.vm_writer.write_pop('pointer', 0)

        # THIS = argument 0 for class methods.
        if self.current_fn_type == 'method':
            self.vm_writer.write_push('argument', 0)
            self.vm_writer.write_pop('pointer', 0)

        # The subroutine body contains statements. For example,
        # let x = Ax;   let statement
        # do draw();    do statement
        # return x;     return statement
        self.compile_statements()

        self.process('}')

    def compile_var_dec(self):
        """
        Compiles a var declaration.
        """
        kind = self.get_token()
        type = self.get_token()

        while self.tokenizer.current_token != ';':
            name = self.get_token()
            self.symbol_table.define(name, type, kind)
            if self.tokenizer.current_token == ',':
                self.process(',')

        self.process(';')

    def compile_statements(self):
        """
        Compiles a sequence of statements.
        """
        # Write statements until ending closing bracket of parent subroutine.
        while self.tokenizer.current_token != '}':
            # Explicitly validate statement
            statement = self.get_token()
            if statement not in self.statements:
                s = ', '.join(self.statements)
                raise SyntaxError('Statement should start with one of ' + s)

            # Compile full statement.
            method = getattr(self, 'compile_' + statement)
            method()

    def compile_let(self):
        """
        Compiles a let statement.
        """
        if self.tokenizer.current_type != 'IDENTIFIER':
            raise SyntaxError('Let statement must proceed with an identifier.')

        identifier = self.get_token()
        index = self.get_index(identifier)
        segment = self.get_kind(identifier)

        # Placement might be an array entring.
        if self.tokenizer.current_token == '[':
            self.compile_array_entry()

            self.vm_writer.write_push(segment, index)
            self.vm_writer.write_arithmetic('ADD')
            self.vm_writer.write_pop('TEMP', 0)

            self.process('=')
            self.compile_expression()

            self.vm_writer.write_push('TEMP', 0)
            self.vm_writer.write_pop('POINTER', 1)
            self.vm_writer.write_pop('THAT', 0)
        else:
            # Regular assignment.
            self.process('=')
            self.compile_expression()
            self.vm_writer.write_pop(segment, index)

        self.process(';')


    def compile_do(self):
        """
        Compiles a do statement.
        """
        self.compile_subroutine_invoke()
        self.vm_writer.write_pop('TEMP', 0)
        self.process(';') # end of do statement.

    def compile_subroutine_invoke(self):
        """
        Compiles a subroutine invokation.
        """
        identifier = self.get_token()
        args_count = 0

        # Either a static (outer) class funciton or an instance function call.
        if self.tokenizer.current_token == '.':
            self.process('.')
            subroutine_name = self.get_token()

            inst_type = self.symbol_table.type_of(identifier)
            if inst_type:
                # It's an instance.
                inst_kind = self.get_kind(identifier)
                inst_indx = self.get_index(identifier)

                self.vm_writer.write_push(inst_kind, inst_indx)
                fn_name = '{}.{}'.format(inst_type, subroutine_name)

                args_count += 1 # Pass 'this' as an argument.
            else: # Static function of a class.
                fn_name = '{}.{}'.format(identifier, subroutine_name)

        else: # Local method call.
            fn_name = '{}.{}'.format(self.classname, identifier)
            args_count += 1 # Pass 'this' as an argument.
            self.vm_writer.write_push('POINTER', 0)

        self.process('(')
        args_count += self.compile_expression_list()
        self.process(')')
        self.vm_writer.write_call(fn_name, args_count)

    def compile_if(self):
        """
        Compiles an if statement, possibly with a trailing else clause.
        """
        self.process('(')
        self.compile_expression() # E.g., x > 2
        self.vm_writer.write_arithmetic('NOT')
        self.process(')') # End of if condition statement.

        # if statement body
        self.process('{')

        idx = self.if_idx
        self.if_idx += 1
        label_false = '{}.if_false.{}'.format(self.current_fn_name, idx)
        label_proceed = '{}.{}'.format(self.current_fn_name, idx)

        self.vm_writer.write_if(label_false)

        self.compile_statements()

        self.vm_writer.write_goto(label_proceed)
        self.process('}')

        # Lables statements.
        self.vm_writer.write_label(label_false)
        if self.tokenizer.current_token == 'else':
            # We have a proceeding else.
            self.process('else')
            self.process('{')
            self.compile_statements()
            self.process('}')

        self.vm_writer.write_label(label_proceed)

    def compile_while(self):
        """
        Compiles a while statement.
        """
        self.process('(')

        fn_name = self.current_fn_name
        idx = self.while_idx
        self.while_idx += 1

        while_start_label = '{}.while_start.{}'.format(fn_name, idx)
        while_end_label = '{}.while_end.{}'.format(fn_name, idx)

        self.vm_writer.write_label(while_start_label)
        self.compile_expression()
        self.vm_writer.write_arithmetic('NOT')
        self.process(')')

        # while's body.
        self.process('{')
        self.vm_writer.write_if(while_end_label)
        self.compile_statements()
        self.vm_writer.write_goto(while_start_label)
        self.vm_writer.write_label(while_end_label)
        self.process('}') # We're done

    def compile_return(self):
        """
        Compiles a return statement.
        """
        if self.tokenizer.current_token != ';':
            self.compile_expression()
        else: # Return VOID.
            self.vm_writer.write_push('CONSTANT', 0)

        self.vm_writer.write_return()
        self.process(';')

    def compile_expression(self):
        """
        Compiles an expression.
        """
        self.compile_term()

        while self.tokenizer.current_token in self.ops:
            op = self.get_token()
            self.compile_term() # Push is done by compile_term

            # Explicitly use Math.multiply or Math.divide.
            if op == '*':
                self.vm_writer.write_call('Math.multiply', 2)
            elif op == '/':
                self.vm_writer.write_call('Math.divide', 2)
            else:
                name = self.verbal_arithemtic.get(op)
                self.vm_writer.write_arithmetic(name)

    def compile_term(self):
        """
        Compiles a term. If the current token is an identifier, the routine
        must resolve it into a variable, an array entry, or a subroutine
        call. A single lookahead token, which may be [, (, or ., suffices
        to distinguish between the possibilities. Any other token is not
        part of this term and should not be advanced over.
        """

        current_token = self.tokenizer.current_token
        token_type = self.get_current_type()

        if current_token == '(':
            self.process('(')
            self.compile_expression()
            self.process(')')
        elif self.tokenizer.peek() == '[':
            arr_identifier = self.get_token()
            self.compile_array_entry()

            index = self.get_index(arr_identifier)
            segment = self.get_kind(arr_identifier)
            self.vm_writer.write_push(segment, index)
            self.vm_writer.write_arithmetic('ADD')
            self.vm_writer.write_pop('POINTER', 1)
            self.vm_writer.write_push('THAT', 0)

        elif current_token in self.unary_ops:
            unary_op = self.get_token()
            self.compile_term()
            name = self.verbal_unary.get(unary_op)
            self.vm_writer.write_arithmetic(name)

        elif self.peek() in ['.', '(']:
            self.compile_subroutine_invoke()

        elif token_type == 'INT_CONST':
            self._compile_integer()
        elif token_type == 'STRING_CONST':
            self._compile_string()
        elif token_type == 'KEYWORD':
            self._compile_keyword()
        else:
            self._compile_identifier()

    def _compile_integer(self):
        """Compiles the current token as an integer."""
        token = self.get_token()
        self.vm_writer.write_push('CONSTANT', abs(token))
        if token < 0:
            self.vm_writer.write_arithmetic('NEG')


    def _compile_string(self):
        """Compiles the current token as a string."""
        current_token = self.tokenizer.current_token
        self.vm_writer.write_push('CONSTANT', len(current_token))
        self.vm_writer.write_call('String.new', 1)

        # String assignments are handled using a series of calls
        # to String.appendChar(c), when c is the integer representing
        # unicode code point.
        for c in current_token:
            self.vm_writer.write_push('CONSTANT', ord(c))
            self.vm_writer.write_call('String.appendChar', 2)

        self.process() # Finished compiling string.

    def _compile_keyword(self):
        """Compiles the current token as a keyword."""
        current_token = self.get_token()
        if current_token == 'this':
            self.vm_writer.write_push('POINTER', 0)
            return

        if current_token == 'true':
            self.vm_writer.write_push('CONSTANT', 1)
            self.vm_writer.write_arithmetic('NEG')
            return

        # null or false.
        self.vm_writer.write_push('CONSTANT', 0)

    def _compile_identifier(self):
        """Compiles the current token as an identifier."""
        current_token = self.get_token()
        index = self.get_index(current_token)
        segment = self.get_kind(current_token)
        self.vm_writer.write_push(segment, index)

    def get_current_type(self):
        """Returns the type of the current token."""
        return self.tokenizer.current_type

    def compile_expression_list(self):
        """
        Compiles a (possibly empty) comma- separated list of expressions
        and returns the number of arguments in this expression list.
        """
        args_count = 0
        while self.tokenizer.current_token != ')':
            args_count += 1
            self.compile_expression()

            if self.tokenizer.current_token == ',':
                self.process(',')

        return args_count

    def process(self, string=None):
        """
        A helper routine that validates the current token,
        and advances to get the next token.
        """

        t = self.tokenizer.current_token
        if string and t != string:
            caller = inspect.stack()[1][3]
            msg = 'Invalid token rasied from {}. Got {} when expected: {}'.format(caller, string, t)
            raise SyntaxError(msg)

        if self.tokenizer.has_more_tokens():
            self.tokenizer.advance()

    def get_token(self):
        """
        Helper method to get the current token and advance
        to the next one.
        """
        token = self.tokenizer.current_token

        if self.tokenizer.has_more_tokens():
            self.tokenizer.advance()

        return token

    def peek(self):
        """Peeks into the toknes deque."""
        return self.tokenizer.peek()

    def compile_array_entry(self):
        """
        A helper routine to compile an array entry.
        """
        self.process('[')
        self.compile_expression()
        self.process(']')

    def is_int(self, input):
        try:
            input = int(input)
            return True
        except ValueError:
            return None

    def get_kind(self, name):
        """Returns the kind value of a symbol table value."""
        segment = self.symbol_table.kind_of(name)
        segment = segment.lower()
        if segment == 'field':
            return 'this'
        if segment == 'var':
            return 'local'
        if segment == 'arg':
            return 'argument'

        return segment

    def get_index(self, name):
        """Returns the index value of a symbol table value."""
        return self.symbol_table.index_of(name)

    def get_classname(self, filename):
        """Returns the clean class name."""
        return filename.split('/')[-1].split('.')[0]

    def close(self):
        """
        Closes the vm stream.
        """
        self.vm_writer.close()
