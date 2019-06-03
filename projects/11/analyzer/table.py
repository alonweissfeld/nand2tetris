class SymbolTable:
    def __init__(self, classname):
        print 'class name:', classname
        self.classname = classname.split('/')[-1]

        self.class_table = {}
        self.subroutine_table = {}

        self.counters = {
            'class': {
                'static': 0,
                'field': 0
            },
            'subroutine': {
                'var': 0,
                'arg': 0
            }
        }

    def start_subroutine(self):
        """
        Resets the subroutine's symbol table.
        """
        self.subroutine_table = {}
        self.counters['subroutine'] = {'var': 0, 'arg': 0}

    def define(self, name, type, kind):
        if kind == 'static' or kind == 'field':
            self.class_table[name] = {
                'type': type,
                'kind': kind,
                'index': self.counters['class'].get(kind)
            }

            self.counters['class'][kind] += 1

        else:
            self.subroutine_table[name] = {
                'type': type,
                'kind': kind,
                'index': self.counters['subroutine'].get(kind)
            }

            self.counters['subroutine'][kind] += 1

    def var_count(self, kind):
        """
        Returns the number of variables of the given kind already
        defined in the current scope.
        """
        type = 'subroutine' if kind in ['var', 'arg'] else 'class'
        return self.counters[type].get(kind)

    def kind_of(self, name):
        """
        Returns the kind of the named identifier in the current scope:
        returns STATIC, FIELD, ARG OR VAR.
        """
        return get_by_hierarchy(name, 'kind')

    def type_of(self, name):
        """
        Returns the type of the named identifier in the current scope.
        """
        return get_by_hierarchy(name, 'type')

    def index_of(self, name):
        """
        Returns the index assigned to the named identifier.
        """
        return get_by_hierarchy(name, 'index')

    def get_by_hierarchy(self, name, attr):
        """
        Helper method to first scout the current scope of the subroutine.
        If it's not there, scout the class symbols and return this attribute.
        Return None if identifier doesn't exit in two if them.
        """
        if name in self.subroutine_table.keys():
            return self.subroutine_table[name].get(attr)

        if name in self.class_table.keys():
            return self.class_table[name].get(attr)

        return None
