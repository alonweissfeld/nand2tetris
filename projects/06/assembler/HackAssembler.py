import re
import sys
from parser import Parser
from code import Code

def main():
    if len(sys.argv) < 2:
        raise Exception("Usage: python HackAssembler.py filename")

    filename = sys.argv[1]
    hack_filename = re.sub('.asm$', '.hack', filename)
    try:
        # Initiate a parser and binary output file.
        hackfile = open(hack_filename, 'w')
        parser = Parser(filename)

        # Initiate a code module helper.
        code = Code()

        while parser.has_more_commands():
            parser.advance()
            command = parser.current_command

            output = None
            t = parser.command_type()

            # Create a binary representation of the current
            # command according to the Hack contract.
            if t == 'C_COMMAND':
                comp = code.comp(parser.comp())
                dest = code.dest(parser.dest())
                jump = code.jump(parser.jump())
                output = '111' + comp + dest + jump

            elif t == 'A_COMMAND':
                symbol = parser.symbol()
                output = format(int(symbol), '016b')

            hackfile.write(output + '\n')

        hackfile.close()
    except IOError, err:
        print("Encountered an I/O Error:", str(err))


if __name__ == '__main__':
    main()
