
class CodeWriter:
    """
    This module translates a parsed VM command into Hack assembly code.
    """
    def __init__(self, filename):
        self.stream = open(filename, 'w')

    def write_arithmetic(self, command):
        """
        Writes to the output file the assembly code that
        implements the given arithmetic-logical command.
        """
        lines = None
        if command == 'add':
            lines = [
                # Decreament Mem[SP] by 1 and store in A as well,
                 # to load the first value into D register.
                '@SP',
                'AM=M-1',
                'D=M',

                # Similiary, pop the second value and sum it with D's value.
                # Save the result in Mem[(2nd value index)]
                '@SP',
                'AM=M-1',
                'M=D+M',

                # Increment SP index by 1. The next item that will be
                # pushed into the Stack, will override the first original
                # value that we popped during 'add'.
                '@SP',
                'M=M+1'
            ]

        self.write_lines(lines)


    def write_push_pop(self, command_type, segment, idx):
        """
        Writes to the output file the assembly code that
        implements the given push or pop command.
        """
        lines = None

        if command_type == 'C_PUSH':
            # Pushes value of segment[idx] to stack

            if segment == 'constant':
                lines = [
                    '@' + str(idx),
                    'D=A',
                    '@SP',
                    'A=M',
                    'M=D',
                    '@SP',
                    'M=M+1'
                ]


        self.write_lines(lines)

    def write_lines(self, lines):
        """
        Given an array of lines, write them to the stream.
        """
        print "got lines?", lines
        if lines == None:
            print 'Can\'t write, given data is null'
            return

        lines.append('')
        self.stream.write('\n'.join(lines))

    def close(self):
        """
        Closes the output file.
        """
        self.stream.close()
