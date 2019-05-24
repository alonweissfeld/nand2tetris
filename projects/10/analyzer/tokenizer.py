import re
from collections import deque

class JackTokenizer:
    """
    Ignores all comments and white space in the input stream, and enables
    accessing the input one token at a time. Also, parses and provides
    the type of each token, as defined by the Jack grammar.
    """
    def __init__(self, filename):
        self.filename = filename
        self.current_token = None
        self.current_type = None

        # Defines a deque collection of all the tokens
        # of the given jack file.
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
        While at it, check for further tokens down the road.
        """
        if not self.has_more_tokens:
            print "No more tokens."
            return

        self.current_token = self.tokens.popleft()
        self.current_type = self.token_type()

    def token_type(self):
        """
        Returns the type of the current token, as a constant.
        Since the type might be ambiguous for expressions like
        field int x,y; We might need to further seperate.
        """
        token = self.current_token

        # Symbols.
        if token[0] in self.symbols:
            self.current_token = self.symbol()
            return 'SYMBOL'

        # String constans.
        if token[0] == '"':
            self.current_token = self.string_val()
            return 'STRING_CONST'

        if token in self.keywords:
            self.current_token = token
            return 'KEYWORD'

        # Int constants.
        int_val = self.int_val()
        if (int_val):
            self.current_token = int_val
            return 'INT_CONST'

        # Identifiers.
        self.current_token = self.identifier()
        # As the whole token might be an expression like:
        # Memory.deAlloc(this), and thus seperated at some stage
        # to 'this)', it wasn't recognized as a keyword.
        return 'KEYWORD' if self.current_token in self.keywords else 'IDENTIFIER'

    def keyword(self):
        """
        Returns the keyword which is the current token, as a constant.
        """
        token = self.current_token
        if (token not in self.keywords):
            raise TypeError('Current token is not a keyword.')

        return self.keywords.get(token)

    def symbol(self):
        """
        Returns the character which is the current symbol token.
        """
        token = self.current_token
        if (token[0] not in self.symbols):
            raise TypeError('Current token is not a symbol.')

        # Support a sequence of tokens, for example "field int x ,y;".
        # Our token might be ,y; and needs to be seperated.
        if len(token) > 1:
            self.tokens.appendleft(token[1:])
            token = token[0]

        return token

    def identifier(self):
        """
        Returns the string which is the current identifier token.
        """
        # We need to check for trailing symbol, for exmaple in case
        # when we declare field int x, y;
        token = self.current_token
        for idx, el in enumerate(token):
            if el in self.symbols:
                # Current identifier reached it's last char.
                self.tokens.appendleft(token[idx:])
                token = token[:idx]
                break

        return token

    def int_val(self):
        """
        Returns the integer value of the current token.
        """
        token = self.current_token
        try:
            token = int(token)
            return token
        except ValueError:
            return None

    def string_val(self):
        """
        Returns the string value of the current token, without the
        opening and closing double quotes.
        """
        token = self.current_token
        if token[0] != '"':
            raise TypeError('Current token is not a string.')

        string = token[1:]
        for idx in range(len(string)):
            if string[idx] == '"':
                # We're done with string.
                string = string[:idx].strip()
                if token[idx + 1:]:
                    self.tokens.appendleft(token[idx + 1:])

        return string

    def peek(self):
        """
        Peek at leftmost item.
        """
        return self.tokens[0]
