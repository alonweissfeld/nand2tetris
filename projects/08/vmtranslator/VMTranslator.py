import re
import os
import sys
import glob

from parser import Parser
from writer import CodeWriter

def main():
    if len(sys.argv) < 2:
        raise Exception("Usage: python VMTranslator.py filename/dirname")

    files = None
    path = sys.argv[1]

    # TODO: If no path is specified, the VM translator operates
    # on the current directory by default.


    # Given path is either a single VM file, or a directory of VM files.
    is_single_file = re.search('.vm$', path)
    if not is_single_file and not os.path.isdir(path):
        raise Exception("Given path is not a directory or valid vm file.")

    if not is_single_file:
        # When invoked with dir_name, create a single output file named
        # dir_name.asm, which is stored in the same directory.
        files = glob.glob(os.path.join(path, '*.vm'))
        path = os.path.join(path, path.split('/')[-1])
    else:
        # We're given a single VM file.
        files = [path]

    try:
        writer = CodeWriter(path)
        writer.write_init()

        for file in files:
            writer.sef_file_name(file)
            translate(writer, file)

        # It is always recommended to end each machine language
        # program with an infinite loop
        writer.terminate()
        writer.close_file()
        print "Done writing assembly code to", re.sub('(.vm)|()$', '.asm', path)

    except IOError, err:
        print "Encountered an I/O Error:", str(err)
    except ValueError, err:
        print "Encountered a Value Error:", str(err)


def translate(writer, filename):
    """
    Translates a single VM file into assembly code.
    """
    parser = Parser(filename)

    while parser.has_more_lines():
        parser.advance()
        command_type = parser.command_type()

        # Write the current vm command as a comment before any assembly code.
        writer.write_lines('// ' + parser.current_command)

        if command_type in ['C_PUSH', 'C_POP']:
            segment = parser.arg1()
            index = parser.arg2()
            writer.write_push_pop(command_type, segment, index)

        if command_type == 'C_ARITHMETIC':
            operation = parser.arg1()
            writer.write_arithmetic(operation)

        arg1 = parser.arg1()
        if command_type == 'C_LABEL':
            writer.write_label(arg1)

        if command_type == 'C_GOTO':
            writer.write_goto(arg1)

        if command_type == 'C_IF':
            writer.write_if(arg1)

    parser.close() # We're done reading from file.


if __name__ == '__main__':
    main()
