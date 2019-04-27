import re
import sys

from parser import Parser
from writer import CodeWriter

def main():
    if len(sys.argv) < 2:
        raise Exception("Usage: python VMTranslator.py filename")

    filename = sys.argv[1]
    if not re.search('.vm$', filename):
        raise Exception("Given file is not a vm file.")

    asm_filename = re.sub('.vm$', '.asm', filename)

    try:
        parser = Parser(filename)
        writer = CodeWriter(asm_filename)

        while parser.has_more_lines():
            parser.advance()
            command_type = parser.command_type()
            print "current line: ", parser.current_command

            if command_type in ['C_PUSH', 'C_POP']:
                segment = parser.arg1()
                index = parser.arg2()
                writer.write_push_pop(command_type, segment, index)

            if command_type == 'C_ARITHMETIC':
                operation = parser.arg1()
                writer.write_arithmetic(operation)

        writer.close()
        print "Done writing assembly code to", asm_filename 

    except IOError, err:
        print "Encountered an I/O Error:", str(err)


if __name__ == '__main__':
    main()
