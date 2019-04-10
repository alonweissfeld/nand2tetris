# The translation of the dest field to it's binary form
dest_codes = {
    None: '000', # Empty destination
    'M': '001',
    'D': '010',
    'MD': '011',
    'A': '100',
    'AM': '101',
    'AD': '110',
    'AMD': '111'
}

# The translation of the comp field to it's binary form
comp_codes = {
    '0': '101010',
    '1': '111111',
    '-1': '111010',
    'D': '001100',
    'A': '110000',
    '!D': '001101',
    '!A': '110001',
    '-D': '001111',
    '-A': '110011',
    'D+1': '011111',
    'A+1': '110111',
    'D-1': '001110',
    'A-1': '110010',
    'D+A': '000010',
    'D-A': '010011',
    'A-D': '000111',
    'D&A': '000000',
    'D|A': '010101'
}

# The translation of the jump field to it's binary form
jump_codes = {
    None: '000', # Empty jump,
    'JGT': '001',
    'JEQ': '010',
    'JGE': '011',
    'JLT': '100',
    'JNE': '101',
    'JLE': '110',
    'JMP': '111'
}


class Code:
    """
    Translates Hack assembly language mnemonics into binary codes.

    note // ASK SHIMON: Why these functions are part of a class?
            'Code' doesn't refelct any entity that requires multiple
            instances. It could be used alternaitvley as helper
            functions as part of this package.
    """
    def __init__(self):
        pass

    def dest(self, string):
        """
        Returns the binary code of the dest mnemonic.
        """
        return dest_codes[string]

    def comp(self, string):
        """
        Returns the binary code of the comp mnemonic.
        """
        # Defines if it's 'A' or 'M' register, in case we use those registers.
        a = '1' if 'M' in string else '0'

        if string is not None:
            string = string.replace('M', 'A')

        return a + comp_codes[string]

    def jump(self, string):
        """
        Returns the binary code of the jump mnemonic.
        """
        return jump_codes[string]
