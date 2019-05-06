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
        # Clean dir_name path, if it ends with a slash.
        if path.endswith('/'):
            path = path[:-1]

        # When invoked with dir_name, create a single output file named
        # dir_name.asm, which is stored in the same directory.
        files = glob.glob(os.path.join(path, '*.vm'))
        path = os.path.join(path, path.split('/')[-1])
    else:
        # We're given a single VM file.
        files = [path]

    try:
        writer = CodeWriter(path)

        # Only inject bootstrap code when dealing with directories.
        if not is_single_file:
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

        arg1 = parser.arg1()
        arg2 = parser.arg2()

        # Defines the proper routine to call upon the given command
        routines = {
            'C_POP': writer.write_push_pop,
            'C_PUSH': writer.write_push_pop,
            'C_ARITHMETIC': writer.write_arithmetic,
            'C_LABEL': writer.write_label,
            'C_GOTO': writer.write_goto,
            'C_IF': writer.write_if,
            'C_FUNCTION': writer.write_function,
            'C_CALL': writer.write_call,
            'C_RETURN': writer.write_return
        }

        routine = routines[command_type]

        if command_type in ['C_PUSH', 'C_POP']:
            routine(command_type, arg1, arg2)

        # Comparing to None explicitly since an argument may be zero.
        elif arg1 is not None and arg2 is not None:
             # C_FUNCTION, C_CALL
            routine(arg1, arg2)
        elif arg1 is not None:
            # C_ARITHMETIC, C_LABEL, C_GOTO, C_IF
            routine(arg1)
        else:
            # C_RETURN
            routine()
    parser.close() # We're done reading from file.


if __name__ == '__main__':
    main()
