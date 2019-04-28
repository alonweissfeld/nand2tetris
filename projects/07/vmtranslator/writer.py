import re

class CodeWriter:
    """
    This module translates a parsed VM command into Hack assembly code.
    """
    def __init__(self, filename):
        filename = re.sub('.vm$', '', filename)
        self.stream = open(filename + '.asm', 'w')
        self.clean_filename = filename.split('/')[-1]

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
