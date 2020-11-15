########################################################################################################################
#
########################################################################################################################
class FilterNode:

    ####################################################################################################################
    #
    ####################################################################################################################
    def __init__(self, name, parent=None):

        self.name:str                   = name
        self.lower_bound:int            = None
        self.upper_bound:int            = None
        self.all:bool                   = False
        self.parent:FilterNode          = parent

        self.children:list[FilterNode]  = []

    ####################################################################################################################
    #
    ####################################################################################################################
    def __str__(self) -> str:
        # if self.all is specified, then just *
        if self.all:
            child_string = '*'
        else:
            # commad delimited list of child __str__ representations
            child_string = ','.join(str(c) for c in self.children)

        # default bound is nothing
        bound = ''

        # user specified both bounds
        if self.lower_bound is not None and self.upper_bound is not None:
            bound = f'{{{self.lower_bound},{self.upper_bound}}}'
        # user specified only lower bound
        elif self.lower_bound is not None:
            bound = f'{{{self.lower_bound},}}'
        # user specified only upper bound
        elif self.upper_bound is not None:
            bound = f',{{{self.upper_bound}}}'

        return f'{self.name}[{child_string}]{bound}'

    ####################################################################################################################
    #
    ####################################################################################################################
    def with_lower_bound(self, lower:int):
        self.lower_bound = lower
        return self

    ####################################################################################################################
    #
    ####################################################################################################################
    def with_upper_bound(self, upper:int):
        self.upper_bound = upper
        return self

    ####################################################################################################################
    #
    ####################################################################################################################
    def with_all(self):
        self.all = True
        return self

    ####################################################################################################################
    #
    ####################################################################################################################
    def begin_child(self, name):
        filter = FilterNode(
            name=name,
            parent=self
        )
        self.children.append(filter)
        return filter

    ####################################################################################################################
    #
    ####################################################################################################################
    def with_child(self, name):
        filter = FilterNode(name=name,parent=self).with_all()
        self.children.append(filter)
        return self

    ####################################################################################################################
    #
    ####################################################################################################################
    def end(self):
        return self.parent if self.parent else self
