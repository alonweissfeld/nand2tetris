
class SymbolTable:
    """
    Keeps a correspondence between symbolic labels and their meaning
    (in Hack’s case, RAM and ROM addresses).
    """
    def __init__(self):
        self.symbols = {}

    def add_entry(self, symbol, address):
        """
        Adds the pair (symbol, address) to the table.
        """
        self.symbols[symbol] = address

    def contains(self, symbol):
        """
        Does the symbol table contain the given symbol?
        """
        return symbol in self.symbols

    def get_address(self, symbol):
        """
        Returns the address associated with the symbol.
        """
        if self.contains(symbol):
            return self.symbols[symbol]

        print "Given symbol does not exist in table."
        return None
