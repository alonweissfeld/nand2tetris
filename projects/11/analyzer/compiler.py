import re
import inspect

from writer import VMWriter
from table import SymbolTable

class CompilationEngine:
    """
    Recursive top-down compilation engine for the Jack langauge.
    Using a Tokenizer object, this module will process different
    Jack tokens and compile it to VM code using the VMWriter.
    While at it, invalid Jack syntax will raise SyntxError.
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
        self.classname = filename.split('/')[-1]

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


    def compile_class(self):
        """
        Compiles a complete class.
        """
        if not self.tokenizer.has_more_tokens():
            raise SyntaxError('No tokens available to compile.')

        self.tokenizer.advance()
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

        # Validates the closing bracket of a class.
        self.process('}')
        self.vm_writer.close()

    def compile_class_var_dec(self):
        """
        Compiles a static variable declaration, or a field declaration.
        """
        kind = self.process()
        type = self.process()

        # Iterate tokens until reaching a command break (';').
        while self.tokenizer.current_token != ';':
            name = self.process()
            self.symbol_table.define(name, type, kind)

            if self.tokenizer.current_token == ',':
                self.process()

        self.process(';')

    def compile_subroutine_dec(self):
        """
        Compiles a complete method, function, or constructor.
        """
        kind = self.process() # static function, method or constructor.
        self.current_fn_type = self.process() # void or type.
        self.current_fn_name = self.process() # name of the subroutine.

        # Reset symbol table for current scope.
        self.symbol_table.start_subroutine()

        if kind == 'method':
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
            type = self.process()
            name = self.process()
            self.symbol_table.define(name, type, 'arg')

            if self.tokenizer.current_token == ',':
                self.process()

        #self.process(';')

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
        kind = self.process('var') # TODO: check if only var?
        type = self.process()

        while self.tokenizer.current_token != ';':
            name = self.process()

            self.symbol_table.define(name, type, kind)
            if self.tokenizer.current_token == ',':
                self.process()

        self.process(';')

    def compile_statements(self):
        """
        Compiles a sequence of statements.
        """
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

    def compile_let(self):
        """
        Compiles a let statement.
        """
        self.process('let')

        if self.tokenizer.current_type != 'IDENTIFIER':
            raise SyntaxError('Let statement must proceed with an identifier.')
        identifier = self.process(self.tokenizer.current_token)

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

            self.write_pop(segment, index)

        self.process(';')


    def compile_do(self):
        """
        Compiles a do statement.
        """
        self.process('do')
        self.compile_subroutine_invoke()
        self.vm_writer.write_pop('TEMP', 0)
        self.process(';') # end of do statement.

    def compile_subroutine_invoke(self):
        """
        Compiles a subroutine invokation.
        """
        identifier = self.process()
        args_count = 0

        # Either a static (outer) class funciton or an instance function call.
        if self.tokenizer.peek() == '.':
            self.process('.')
            subroutine_name = self.process()

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
        self.process('if')
        self.process('(')
        self.compile_expression() # E.g., x > 2
        self.vm_writer.write_arithmetic('NOT')
        self.process(')') # End of if condition statement.

        # if statement body
        self.process('{')

        idx = self.if_idx
        self.if_idx += 1
        label_false = '{}.IF_FALSE.{}'.format(self.current_fn_name, idx)
        label_proceed = '{}.{}'.format(self.current_fn_name, idx)

        self.vm_writer.write_if(label_false)

        self.compile_statements()

        self.vm_writer.write_goto(label_proceed)
        self.process('}')

        # Lables statements.
        self.vm_writer.write_line(label_false)
        if self.tokenizer.current_token == 'else':
            # We have a proceeding else.
            self.process('else')
            self.process('{')
            self.compile_statements()
            self.process('}')

        self.vm_writer.write_line(label_proceed)

    def compile_while(self):
        """
        Compiles a while statement.
        """
        self.process('while')
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

    def process(self, string=None):
        """
        A helper routine that handles the current token,
        and advances to get the next token.
        """
        if string and self.tokenizer.current_token != string:
            caller = inspect.stack()[1][3]
            msg = 'Invalid token found in {}, expected: {}'.format(caller, string)
            raise SyntaxError(msg)

        current = self.tokenizer.current_token

        if self.tokenizer.has_more_tokens():
            self.tokenizer.advance()

        return current

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

    def get_kind(self, name):
        segment = self.symbol_table.kind_of(name)

        if segment == 'FIELD':
            return 'THIS'
        if segment == 'VAR':
            return 'LOCAL'

        return segment

    def get_index(self, name):
        return self.symbol_table.index_of(name)

    def close(self):
        """
        Closes this stream.
        """
        self.xml.close()
