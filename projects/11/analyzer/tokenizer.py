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

        # Remove API comments (/** some comment here.. */)
        data = re.sub('(/\*{2,}(\n|.*?)*?\*/)*', '', data)

        data = data.split('\n') # Split by new line
        data = [l.strip() for l in data] # Strip white space
        data = [l.split('//')[0] for l in data ] # Remove inline comments

        # We have filtered all the lines of the file to just code.
        # Now, make a final tokens array - seperated as words.
        tokens = []
        for line in data:
            if not line:
                continue

            # Handle strings - shouldn't be seperated by white space.
            if '"' not in line:
                tokens.extend(line.split())
                continue

            # Current line includes a string.
            try:
                start_idx, end_idx = (m.start() for m in \
                    re.finditer(r'"', line))

                if line[:start_idx]:
                    tokens.extend(line[:start_idx].split())

                # The string itself.
                tokens.append(line[start_idx:end_idx + 1])

                if line[end_idx + 1:]:
                    tokens.extend(line[end_idx + 1:].split())

            except ValueError:
                raise SyntaxError('Invalid Jack string.')

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
        if not self.has_more_tokens():
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

        # String constans.
        if token[0] == '"':
            self.current_token = self.string_val()
            return 'STRING_CONST'

        if token in self.keywords:
            self.current_token = token
            return 'KEYWORD'

        # Int constants.
        int_val = self.int_val()
        if int_val is not None: # Integer might be zero.
            self.current_token = int_val
            return 'INT_CONST'

        # Symbols.
        if token[0] in self.symbols:
            self.current_token = self.symbol()
            return 'SYMBOL'

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

        sign = None
        if token[0] == '-':
            sign = True
            token = token[1:]

        if not token or not token[0].isdigit():
            return None

        # We have a digit token, potentially, but we need
        # to verify it or find trailing symbols.
        integer = None
        for idx, el in enumerate(token):
            if not el.isdigit() or el in self.symbols:
                integer = int(token[:idx])
                self.tokens.appendleft(token[idx:])
                break
            else:
                integer = int(token[:idx + 1])

        if sign:
            integer = -1 * integer
        return integer

    def string_val(self):
        """
        Returns the string value of the current token, without the
        opening and closing double quotes.
        """
        token = self.current_token
        if token[0] != '"':
            raise TypeError('Current token is not a string.')

        idx = token[1:].find('"')
        if idx < 0:
            raise SyntaxError('Invalid string.')

        string = token[1:idx + 1]

        # Check trailing tokens.
        if token[idx + 2:]:
            self.tokens.appendleft(token[idx + 1:])

        return string

    def peek(self):
        """
        Peek at leftmost item in the tokens deque.
        """
        return self.tokens[0]

    def seperate_all(self):
        """
        Since some of our tokens are further seperated only when advancing
        (for example, we may currently have a token like 'Keyboard.readInt('),
        this method goes over all tokens and preforms the complete seperation.
        This can help in the compiling prorcess since we're validating
        specific tokens throughout the process.
        """
        tokens = []
        while self.has_more_tokens():
            self.advance()
            token = self.current_token
            if self.current_type == 'STRING_CONST':
                token = '"{}"'.format(token)
            tokens.append(str(token))

        self.tokens = deque(tokens)
