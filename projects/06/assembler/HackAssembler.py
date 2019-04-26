import re
import sys
from parser import Parser
from code import Code
from symbols import SymbolTable

def main():
    """
    Transforms a program written in assembly code into binary machine code
    that can be run on the Hack hardware.
    """
    if len(sys.argv) < 2:
        raise Exception("Usage: python HackAssembler.py filename")

    filename = sys.argv[1]
    hack_filename = re.sub('.asm$', '.hack', filename)

    try:
        # Initiate a parser and binary output file.
        hackfile = open(hack_filename, 'w')
        parser = Parser(filename)

        # Initiate a code and symbol table modules.
        code = Code()
        table = SymbolTable()

        # Determines the ROM count (actuall program instructions). Incremented
        # whenever a C-instruction or an A-instruction is encountered.
        instructions_count = 0

        # First pass - build the symbol table without generating any code
        while parser.has_more_commands():
            parser.advance()

            command = parser.current_command
            t = parser.command_type()

            if t == 'L_COMMAND':
                # Add a new entry to the symbol table, associating
                # Xxx with the ROM address that will eventually
                # store the next command in the program
                symbol = parser.symbol()
                table.add_entry(symbol, instructions_count)
            else:
                instructions_count += 1

        # Second pass - Parse each line
        parser.rollback()
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

                if not symbol.isdigit():
                    if not table.contains(symbol):
                        table.add_entry(symbol, table.next_ram_addr)
                        table.next_ram_addr += 1

                    # Get the symbol numeric meaning
                    symbol = table.symbols[symbol]

                output = format(int(symbol), '016b')

            if output is not None:
                hackfile.write(output + '\n')

        print "Done writing (binary) hack file: {0}".format(hack_filename)
        hackfile.close()
    except IOError, err:
        print "Encountered an I/O Error:", str(err)


if __name__ == '__main__':
    main()
