import re

class VMWriter:
    def __init__(self, filename):
        self.stream = re.sub('.jack$', '.vm', filename)

    def write_push(self, segment, index):
        segment = segment.lower()
        self.write_line('push {} {}'.format(segment, index))

    def write_pop(self, segment, index):
        segment = segment.lower()
        self.write_line('pop {} {}'.format(segment, index))

    def write_arithmetic(self, command):
        command = command.lower()
        self.write_line(command)

    def write_label(self, label):
        self.write_line('label {}'.format(label))

    def write_goto(self, label):
        self.write_line('goto {}'.format(label))

    def write_if(self, label):
        self.write_line('if-goto {}'.format(label))

    def write_call(self, name, nargs):
        self.write_line('call {} {}'.format(name, nargs))

    def write_function(self, name, nlocals):
        self.write_line('call {} {}'.format(name, nlocals))

    def write_return(self):
        self.write_line('return')

    def write_line(self, line):
        self.stream.write(line + '\n')

    def close(self):
        """
        Closes the output file.
        """
        self.stream.close()
