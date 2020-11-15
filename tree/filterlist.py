########################################################################################################################
#
########################################################################################################################
from .filternode import FilterNode


########################################################################################################################
#
########################################################################################################################
class FilterList:

    ####################################################################################################################
    #
    ####################################################################################################################
    def __init__(self):
        self.filters:list[FilterNode] = []

    ####################################################################################################################
    #
    ####################################################################################################################
    def __str__(self) -> str:
        return f"{','.join([str(f) for f in self.filters])}"

    ####################################################################################################################
    #
    ####################################################################################################################
    def with_filter(self, name) -> FilterNode:
        self.add_filter(name)
        return self.filters[-1]

    ####################################################################################################################
    #
    ####################################################################################################################
    def add_filter(self, name):
        self.filters.append(FilterNode(name))
        return self
