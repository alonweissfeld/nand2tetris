import re

class Parser:
    """
    Encapsulates access to the input code. Reads an assembly
    language command, parses it, and provides convenient
    access to the command's components (fields and symbols).
    In addition, removes all white space and comments.
    """

    def __init__(self, filename):
        self.stream = open(filename, 'r')
        self.current_command = None

    def has_more_commands(self):
        """
        Return true if there are more commands in the input file.
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
        Returns the type of the current command.
        """
        cmnd = self.current_command
        if cmnd[0] == '@':
            return 'A_COMMAND'
        if '=' in cmnd or ';' in cmnd:
            return 'C_COMMAND'
        if re.search(r"^\(.+\)$", cmnd) is not None:
            return 'L_COMMAND'

        return 'UNKNOWN_COMMAND'

    def symbol(self):
        """
        Returns the symbol or decimal Xxx of the
        current command @Xxx or (Xxx)
        """
        t = self.command_type()
        if t != 'A_COMMAND' and t != 'L_COMMAND':
            print "Cannot resolve symbol for not a A_COMMAND or L_COMMAND'"
            return

        if t == 'A_COMMAND':
            return self.current_command[1:]
        if t == 'L_COMMAND':
            return self.current_command[1:-1]

    def dest(self):
        """
        Returns the dest mnemonic in the current C-command.
        """
        t = self.command_type()
        if t != 'C_COMMAND':
            print "Cannot resolve dest for a %s" % t
            return

        if '=' not in self.current_command:
            # Destination might be empty, that's fine.
            return None

        return self.current_command.split('=')[0]

    def comp(self):
        """
        Returns the comp mnemonic in the current C-command.
        """
        t = self.command_type()
        if t != 'C_COMMAND':
            print "Cannot resolve comp for a %s" % t
            return

        # return re.search(r"={0,1}([^;=]+);{0,1}", self.current_command).group(1)

        if '=' in self.current_command:
            return self.current_command.split('=')[1]

        return self.current_command.split(';')[0]


    def jump(self):
        """
        Returns the jump mnemonic in the current C-command.
        """
        t = self.command_type()
        if t != 'C_COMMAND':
            print "Cannot resolve comp for a %s" % t
            return

        if ';' not in self.current_command:
            # Jump might be empty, that's fine.
            return None

        return self.current_command.split(';')[1]

    def rollback(self):
        """
        Rolls back the file pointer to the start of the file.
        """
        self.stream.seek(0)
