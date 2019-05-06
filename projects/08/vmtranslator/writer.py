import re

class CodeWriter:
    """
    This module translates a parsed VM command into Hack assembly code.
    """
    def __init__(self, filename):
        # Determines the main stream assembly file to write to.
        filename = re.sub('.vm$', '', filename)
        self.stream = open(filename + '.asm', 'w')

        # Determines the current vm file (without full path) being translated.
        self.current_vmfile = None

        # Defines our VM memory segments. Each segment offers direct
        # access to its base values using it's name, which will be
        # followed later by an index that starts at 0.
        self.addresses = {
            'local': 'LCL',
            'argument': 'ARG',
            'this': 'THIS',
            'that': 'THAT',
            'pointer': 3,
            'temp': 5, # R5-12 Holds temp
            # R13-15 are free
            'static': 16, # R16-255 Holds static vars.
        }

        # Determines the label index of a new encountered boolean operation,
        # and therefore counts the amount of boolean operations so far.
        self.boolean_idx = 0

        # Detremines the 'call' commands that occured so far, within
        # each function. Each function name is uniquely set by
        # file_name.function.name
        self.function_calls_count = {}

    def sef_file_name(self, filename):
        """
        Informs that the translation of a new VM file has started.
        """
        name = filename.replace('.vm', '').split('/')[-1]
        line = '// Translation begins for file: {}'.format(name)

        self.current_vmfile = name
        self.write_lines(line)

    def write_init(self):
        """
        Writes the assembly instructions that effect the bootstrap code
        that starts the program's execution. This code is placed
        at the beginning of the generated .asm file.
        """
        pass

    def write_label(self, label):
        """
        Writes assembly code that effects the label command.
        """
        if not label:
            raise ValueError('No label specified.')

        line = '({0}${1})'.format(self.current_vmfile, label)
        self.write_lines(line)

    def write_goto(self, label):
        """
        Writes assembly code that effects the goto command.
        """
        if not label:
            raise ValueError('No label specified.')

        self.write_lines([
            '@{0}${1}'.format(self.current_vmfile, label),
            '0;JMP'
        ])

    def write_if(self, label):
        """
        Writes assembly code that effects the if-goto command.
        """
        if not label:
            raise ValueError('No label specified.')

        # Pops topmost value from the stack to D register and
        # jumps to the specified label if it's true (Not Equal zero)
        self.write_lines([
            '@SP',
            'AM=M-1', # Decreament SP and set A register to that value.
            'D=M',
            '@{0}${1}'.format(self.current_vmfile, label),
            'D;JNE'
        ])

    def write_function(self, function_name, num_vars):
        """
        Writes assembly code that effects the function command.
        Generates code that declares a function and initializes
        the local variables of the called function.
        """
        # The handling of each "function foo" command within a VM file X
        # generates and injects into the assembly code stream a symbol X.foo
        # that labels the entry- point to the function's code.
        lines = ['({0}.{1})'.format(self.current_vmfile, function_name)]

        # Initialize local vars to 0
        for k in range(num_vars):
            lines += [
                'D=0',
                '@SP', # Write data to top of the stack.
                'A=M',
                'M=D',
                '@SP', # Increment SP
                'M=M+1'
            ]

        self.write_lines(lines)

    def write_call(self, function_name, num_args):
        """
        Writes assembly code that effects the call command.
        Generates code that saves the frame of the caller on the stack,
        sets the segment pointers for the called function, and jumps
        to execute the latter.
        """
        # The handling of each call command within foo's code generates and
        # injects into the assembly code stream a symbol Xxx.foo$ret.i,
        # where i is a running integer (one such symbol is generated
        # for each call command within foo).

        name = '{0}.{1}'.format(self.current_vmfile, function_name)
        if name not in self.function_calls_count:
            self.function_calls_count[name] = 0

        idx = self.function_calls_count[name]
        ret_symbol = '@{0}$ret.{1}'.format(name, idx)

        # Increment call count by 1, for this function.
        self.function_calls_count[name] += 1

        # Push return-address to stack.
        lines += [
            '@' + ret_symbol,
            'D=A',
            '@SP', # Write data to top of the stack.
            'A=M',
            'M=D',
            '@SP', # Increment SP
            'M=M+1'
        ]

        # Save LCL, ARG, THIS and THAT of the caller
        for addr in ['LCL', 'ARG', 'THIS', 'THAT']:
            lines += [
                '@' + addr,
                'D=M',
                '@SP',
                'A=M',
                'M=D',
                '@SP',
                'M=M+1'
            ]

        # Reposition ARG (= SP-n- 5)
        lines += [
            '@SP',
            'D=M',
            '@{}'.format(num_args + 5),
            'D=D-A',
            '@ARG',
            'M=D'
        ]

        # Reposition LCL = SP
        lines += [
            '@SP',
            'D=M',
            '@LCL',
            'M=D'
        ]

        # Transfers control to the called function - goto function.
        lines += [
            '@' + name,
            '0;JMP'
        ]

        # Injects the return-address label into the code
        lines.append('({})'.format(ret_symbol))

        self.write_lines(lines)

    def write_return(self):
        """
        Writes assembly code that effects the return command.
        Generates code that copies the return value to the top of the
        caller's working stack, reinstates the segment pointers of the caller,
        and jumps to execute the latter, from the return address onward.
        """
        # Defines the temporary variables
        frame = 'R13'
        ret = 'R14'

        # frame = LCL
        lines = [
            '@LCL',
            'D=M',
            '@' + frame,
            'M=D'
        ]

        # Puts the return address in a temp variable (=frame-5)
        lines += [
            '@' + frame,
            'D=M',
            '@5',
            'AD=D-A', # Calc address.
            'D=M', # Store address value.
            '@' + ret,
            'M=D' # Save value in temporary return.
        ]

        # Repositions the return value for the caller (ARG = pop())
        lines += [
            '@SP',
            'AM=M-1',
            'D=M',
            '@ARG',
            'A=M',
            'D=M'
        ]

        # Repositions the caller's SP (SP = ARG+1)
        lines += [
            '@ARG',
            'D=M+1',
            '@SP',
            'M=D'
        ]

        # Restores the caller's THAT, THIS, ARG, LCL:
        # THAT = *(FRAME-1)
        # THIS = *(FRAME-2)
        # ARG = *(FRAME-3)
        # LCL = *(FRAME-4)
        for idx, addr in enumerate(['THAT', 'THIS', 'ARG', 'LCL']):
            lines += [
                '@' + frame,
                'D=M',
                '@' + str(idx + 1),
                'AD=D-A',
                'D=M', # Store address value.
                '@' + addr,
                'M=D' # Save value.
            ]

        # goto return address (in the caller's code).
        lines += [
            '@' + ret,
            'A=M',
            '0;JMP'
        ]

        self.write_lines(lines) # We're done.

    def write_arithmetic(self, command):
        """
        Writes to the output file the assembly code that
        implements the given arithmetic-logical command.
        """
        lines = []
        if command not in ['neg', 'not']:
            # Decreament Mem[SP] by 1 and store address in A,
            # to load the first value into D register.
            lines += [
                '@SP',
                'AM=M-1',
                'D=M'
            ]

        # Decreament Mem[SP] by 1 and store address in A
        lines += [
            '@SP',
            'AM=M-1'
        ]

        # Now, according to the given operation, sum/difference or preform
        # bitwise operations between the two values (or just the topmost
        # value that we got if it's not/neg). This will save the result
        # in Mem[(2nd value index)]
        if command == 'add':
            lines.append('M=D+M')
        elif command == 'sub':
            lines.append('M=M-D')
        elif command == 'neg':
            lines.append('M=-M')
        elif command == 'not':
            lines.append('M=!M')
        elif command == 'or':
            lines.append('M=D|M')
        elif command == 'and':
            lines.append('M=D&M')
        elif command in ['eq', 'lt', 'gt']:
            # We'll handle boolean operators with specific labeling for each
            # comparing operation that occured so far.
            bool_idx = str(self.boolean_idx)
            lines += [
                'D=M-D',
                '@BOOLTRUE' + bool_idx
            ]

            # D is (x-y). If x equlas y, then D should be 0. Similarly,
            # if x is bigger than y, D is postivie. If x is smaller than y,
            # D is negative.
            d = {
                'eq': 'D;JEQ',
                'gt': 'D;JGT',
                'lt': 'D;JLT'
            }

            # If the condition answers the criteria we'll jump to BOOLTRUE
            # label and set the topmost value of the stack to True.
            # Otherwise, we'll set it as False and jump to ENDBOOL.
            lines += [
                d[command],
                '@SP',
                'A=M',
                'M=0', # False
                '@ENDBOOL' + bool_idx,
                '0;JMP',

                '(BOOLTRUE{})'.format(bool_idx),
                '@SP',
                'A=M',
                'M=-1', # True

                '(ENDBOOL{})'.format(bool_idx)
            ]

            self.boolean_idx += 1
        else:
            raise ValueError('{} is an invalid arithmetic operation.'.format(command))

        # Finally, increment SP index by 1.  IThe next item that will be
        # pushed into the Stack, will override the first original
        # value that we used during any arithmetic calculation.
        lines += [
            '@SP',
            'M=M+1'
        ]

        self.write_lines(lines)


    def write_push_pop(self, command_type, segment, idx):
        """
        Writes to the output file the assembly code that
        implements the given push or pop command.
        """
        # Calculate relevant address and resolve it to A register.
        lines = []
        lines.append(self.calc_addr(segment, idx))

        if command_type == 'C_PUSH':
            # Pushes value of segment[idx] to stack
            lines += [
                'D=A' if segment == 'constant' else 'D=M',

                # Get the current Stack pointer and set address to it's value.
                '@SP',
                'A=M',

                # Write data to the top of the stack and increment SP.
                'M=D',
                '@SP',
                'M=M+1'
            ]

        elif command_type == 'C_POP':
            # Pops the stack value and stores it in segment[idx]

            lines += [
                # Store resolved address in R13
                'D=A',
                '@R13',
                'M=D',

                 # Decrement SP, and pop topmost value from stack onto D
                 '@SP',
                 'AM=M-1',
                 'D=M',

                 # Get back the address from R13, and save the popped value
                 # in the relevant RAM[addr]
                 '@R13',
                 'A=M',
                 'M=D'
            ]

        self.write_lines(lines)

    def calc_addr(self, segment, idx):
        """
        Calculates the relevant address to the A register.
        """
        result = None
        addr = self.addresses.get(segment)

        if segment == 'constant':
            result = '@' + str(idx)
        elif segment == 'static':
            result = '@' + self.clean_filename + '.' + str(idx)
        elif segment in ['pointer', 'temp']:
            # The pointer and temp segments base values are used as the
            # initial data holders themselves. Therefore, the address
            # is an integer and we want to sum it with the given index.
            result = '@' + str(addr + int(idx))
        elif segment in ['local', 'argument', 'this', 'that']:
            result = '\n'.join([
                # Load the segment base value into D register
                # and sum it with index.
                '@' + addr,
                'D=M',
                '@' + str(idx),
                'A=D+A'
            ])

        if not result:
            raise ValueError('{} is an invalid segment'.format(segment))

        return result

    def write_lines(self, lines):
        """
        Given an array of lines, write them to the stream.
        """
        if lines == None:
            print 'Can\'t write, given data is null'
            return

        # Accept strings as is, wrap it as an array
        if lines and isinstance(lines, str):
            lines = [lines]

        lines.append('')
        self.stream.write('\n'.join(lines))

    def terminate(self):
        """
        End the program with an infinite loop.
        """
        lines = [
            '(END)',
            '@END',
            '0;JMP // Infinite loop'
        ]

        self.write_lines(lines)

    def close_file(self):
        """
        Closes the output file.
        """
        self.stream.close()
