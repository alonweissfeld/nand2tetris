import re

class CompilationEngine:
    """
    Emits a structured representation of the input source code,
    wrapped in XML tags.
    """
    def __init__(self, filename):
        """
        Creates a new compilation engine with the given input and output.
        """
        filename = re.sub('.jack$', '1.xml', filename)
        self.xml = open(filename, 'w')

    def write_token(self, token, type):
        """
        Helper method to write a given token as an xml tag,
        defined by the given type.
        """
        # Support standart XML representation.
        token = token.replace('>', '&gt;')
        token = token.replace('<', '&lt;')
        token = token.replace('&', '&amp;')

        type = type.lower()
        line = '<{}> {} </{}>'.format(type, token, type)
        self.write_line(line)

    def write_line(self, line):
        """
        Write any given text line to the xml.
        """
        self.xml.write(line + '\n')

    def close(self):
        """
        Closes this stream.
        """
        self.xml.close()
