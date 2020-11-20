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
    def get(self, url:str, params:dict[str,str]={}, filter:FilterList=None, depth=0) -> Response:

        local_params = dict(params)

        local_params['depth'] = depth

        # apply tree filter if any
        if filter:
            local_params['tree'] = f'{str(filter)}'

        return super().get(url, params=local_params)
