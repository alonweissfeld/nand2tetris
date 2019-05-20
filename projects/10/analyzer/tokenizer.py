from collections import deque

class JackTokenizer:
    """
    Ignores all comments and white space in the input stream, and enables
    accessing the input one token at a time. Also, parses and provides
    the type of each token, as defined by the Jack grammar.
    """
    def __init__(self, filename):
        self.filename = open(filename, 'r')
        self.current_token = None
        self.tokens = self.init()

        # Defines the symbols characters as part of the Jack langauge.
        self.symbols = [
            '{', '}', '(', ')', '[', ']',
            '.', ',', ';', '+', '-',
            '*', '/', '&', '|', '<',
            '>', '=', '~'
        ]

        # Defines the saved keywords as part of the Jack langauge.
        self.keywords = {
            'class': 'CLASS',
            'constructor': 'CONSTRUCTOR',
            'function': 'FUNCTION',
            'method': 'METHOD',
            'field': 'FIELD',
            'static': 'STATIC',
            'var': 'VAR',
            'int': 'INT',
            'char': 'CHAR',
            'boolean': 'BOOLEAN',
            'void': 'VOID',
            'true': 'TRUE',
            'false': 'FALSE',
            'null': 'NULL',
            'this': 'THIS',
            'let': 'LET',
            'do': 'DO',
            'if': 'IF',
            'else': 'ELSE',
            'while': 'WHILE',
            'return': 'RETURN'
        }

    def init(self):
        """
        Opens the associated jack file and marches through the text
        to filter out comments, white space and new lines.
        Returns a collections.deque object for simplicty as later used.
        """
        with open(self.filename, 'r') as f:
            data = f.read()

        data = data.split('\n') # Split by new line
        data = [l.strip() for l in data] # Strip white space
        data = [l.split('//')[0] for l in data ] # Remove inline comments

        # Remove comment until closing or API comments.
        within_comment = False
        for idx, line in enumerate(data):
            if '/*' in line:
                # This line is a comment or alternatively - there
                # is a comment amidst the line.
                data[idx] = re.sub('/\*.*$', '', line).strip()
                within_comment = True

            if within_comment:
                # The complete line is a comment.
                data[idx] = ''

            if '*/' in line:
                # Comment closure.
                data[idx] = re.sub('\*/.*$', '', line).strip()
                within_comment = False

        # We have filtered all the lines of the file to just code.
        # Now, make a final tokens array - seperated as words.
        tokens = []
        for line in data:
            if line:
                tokens.extend(line.split())

        return deque(tokens)

    def has_more_tokens(self):
        """
        Are there any more tokens in the input?
        """
        return len(self.tokens) > 0

    def advance(self):
        """
        Gets the next token from the input, and makes it the current token.
        """
        if not self.has_more_tokens:
            print "No more tokens."
            return

        self.current_token = self.tokens.popleft()

    def token_type(self):
        """
        Returns the type of the current token, as a constant.
        """
        token = self.current_token

        if token in self.symbols:
            return 'SYMBOL'

        if token in self.keywords:
            return 'KEYWORD'

        if '"' in token:
            return 'STRING_CONST'

        try:
            token = int(token)
            return 'INT_CONST'
        except ValueError:
            return 'IDENTIFIER'
