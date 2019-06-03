import re

class VMWriter:
    """
    Emits VM code into the <classname>.vm file.
    """
    def __init__(self, filename):
        """Creates a new <filename>.vm file and prepares it for writing."""
        self.filename = re.sub('.jack$', '.vm', filename)
        self.stream = open(self.filename, 'w')

    def write_push(self, segment, index):
        """Writes a VM push command."""
        self.write_line('push {} {}'.format(segment, index))

    def write_pop(self, segment, index):
        """Writes a VM pop command."""
        segment = segment.lower()
        self.write_line('pop {} {}'.format(segment, index))

    def write_arithmetic(self, command):
        """Writes a VM arithemtic-logical command."""
        command = command.lower()
        self.write_line(command)

    def write_label(self, label):
        """Writes a VM label command."""
        self.write_line('label {}'.format(label))

    def write_goto(self, label):
        """Writes a VM goto command."""
        self.write_line('goto {}'.format(label))

    def write_if(self, label):
        """Writes a VM if-goto command."""
        self.write_line('if-goto {}'.format(label))

    def write_call(self, name, nargs):
        """Writes a VM call command."""
        self.write_line('call {} {}'.format(name, nargs))

    def write_function(self, name, nlocals):
        """Writes a VM function command."""
        self.write_line('function {} {}'.format(name, nlocals))

    def write_return(self):
        """Writes a VM return command."""
        self.write_line('return')

    def write_line(self, line):
        """Helper routine to write input to the VM output file."""
        self.stream.write(line + '\n')

    def close(self):
        """Closes the output file."""
        self.stream.close()
