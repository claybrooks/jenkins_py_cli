########################################################################################################################
#
########################################################################################################################
from .api                   import API
from network.communicator   import Communicator
from .tree.filterlist        import FilterList
from .tree.filternode        import FilterNode
from requests.models        import Response


########################################################################################################################
#
########################################################################################################################
class TreeAPI(API):

    ####################################################################################################################
    #
    ####################################################################################################################
    def __init__(self, url_base:str, communicator:Communicator):
        super().__init__(url_base=url_base, communicator=communicator)

    ####################################################################################################################
    #
    ####################################################################################################################
    def get(self, url:str, params:dict[str,str]={}, filter:FilterList=None) -> Response:

        # apply tree filter if any
        if filter:
            params['tree'] = f'{str(filter)}'

        return super().get(url, params=params)

    ####################################################################################################################
    #
    ####################################################################################################################
    def info(self, url:str, depth:int=0, params:dict[str,str]={}, filter:FilterList=None) -> Response:
        params['depth'] = depth
        return self.get(url, params=params, filter=filter)