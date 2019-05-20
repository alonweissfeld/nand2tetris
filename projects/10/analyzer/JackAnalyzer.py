import re
import os
import sys
import glob

from parser import Parser
from writer import CodeWriter

def main():
    path = None
    files = None

    # If no path is specified, the Jack Analyzer operates on the
    # current directory by default.
    if len(sys.argv) == 1:
        path = os.getcwd()
    elif len(sys.argv) == 2:
        path = sys.argv[1]
    else:
        raise Exception("Usage: python JackAnalyzer.py filename/dirname " +
            "(empty path for current dir)")

    # Given path is either a single Jack file, or a directory of Jack files.
    is_single_file = re.search('.jack$', path)
    if not is_single_file and not os.path.isdir(path):
        raise Exception("Given path is not a directory or valid jack file.")

    if not is_single_file:
        # Clean dir_name path, if it ends with a slash.
        if path.endswith('/'):
            path = path[:-1]


        # Use all files in direcotry.
        files = glob.glob(os.path.join(path, '*.jack'))
    else:
        # We're given a single Jack file.
        files = [path]

    try:
        # Analyze each jack file.
        pass

    except IOError, err:
        print "Encountered an I/O Error:", str(err)
    except ValueError, err:
        print "Encountered a Value Error:", str(err)


if __name__ == '__main__':
    main()
