import re

class Parser:
    """
    This module handles the parsing of a single .vm file.
    The parser provides services for reading a VM command, unpacking the
    command into its various components,  and providing convenient access
    to these components.  In addition, the parser ignores all white
    space and comments.
    """

    def __init__(self, filename):
        self.stream = open(filename, 'r')
        self.current_command = None

    def has_more_lines(self):
        """
        Return true if there are more lines in the input file.
        """
        pos = self.stream.tell()
        res = self.stream.readline() != ''
        self.stream.seek(pos)
        return res

    def advance(self):
        """
        Reads the next command from the input and makes
        it the current command.
        """
        line = self.stream.readline()
        while line is not None:
            # Strip comments or empty spaces
            line = re.sub('//.*', '', line).strip()

            # Avoid comments or empty lines
            if line != '':
                break

            line = self.stream.readline()

        if line is None:
            print "No more commands."
            return

        self.current_command = line

    def command_type(self):
        """
        Returns a constant representing the type of the current command.
        """
        t = self.current_command.split(' ')[0]
        if t in ['add', 'sub', 'neg', 'eq', 'gt', 'lt', 'and', 'or', 'not']:
            return 'C_ARITHMETIC'

        if t == 'push':
            return 'C_PUSH'

        if t == 'pop':
            return 'C_POP'

        # The following are pre-implementation of project 8.
        if t == 'label':
            return 'C_LABEL'

        if t == 'goto':
            return 'C_GOTO'

        if t == 'if-goto':
            return 'C_IF'

        if t == 'function':
            return 'C_FUNCTION'

        if t == 'return':
            return 'C_RETURN'

        if t == 'call':
            return 'C_CALL'

        return 'UNKNOWN_COMMAND'

    def arg1(self):
        """
        Returns the first argument of the current command.
        """
        t = self.command_type()
        if t == 'C_RETURN':
            return

        args = self.current_command.split(' ')

        if t == 'C_ARITHMETIC':
            # Return the command itself.
            return args[0]

        return args[1]


    def arg2(self):
        """
        Returns the second argument of the current command.
        """
        t = self.command_type()
        if t not in ['C_PUSH', 'C_POP', 'C_FUNCTION', 'C_CALL']:
            return

        return int(self.current_command.split(' ')[2])

    def rollback(self):
        """
        Rolls back the file pointer to the start of the file.
        """
        self.stream.seek(0)
