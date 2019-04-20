
class SymbolTable:
    """
    Keeps a correspondence between symbolic labels and their meaning
    (in Hack’s case, RAM and ROM addresses).
    """
    def __init__(self):
        # Pre-defined symbols.
        self.symbols = {
            'SP': 0,
            'LCL': 1,
            'ARG': 2,
            'THIS': 3,
            'THAT': 4,
            'SCREEN': 16384,
            'KBD': 24576
        }

        # Add R0-R15 RAM locations. Note that each one of the top
        # five RAM locations can be referred to using two predefined symbols.
        # For example, either R2 or ARG can be used to refer to RAM[2].
        for i in range(0, 16):
            self.symbols['R' + str(i)] = i

        # Variables are mapped to consecutive memory locations as
        # they are first encountered, starting at RAM address 16.
        self.next_ram_addr = 16

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
