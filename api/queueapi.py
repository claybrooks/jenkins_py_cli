########################################################################################################################
#
########################################################################################################################
from requests.models        import Response
from network.communicator   import Communicator
from api.treeapi            import TreeAPI
from .tree.filterlist       import FilterList

########################################################################################################################
#
########################################################################################################################
class QueueAPI(TreeAPI):

    ####################################################################################################################
    #
    ####################################################################################################################
    def __init__(self, url_base:str, communicator:Communicator):
        super().__init__(url_base=url_base, communicator=communicator)
        self.info_extension         = f'/queue{self.format}'
        self.item_info_extension    = f'/queue/item/{{}}{self.format}'

    ####################################################################################################################
    #
    ####################################################################################################################
    def info(self, **kwargs) -> Response:
        return self.get(self.info_extension, **kwargs)

    ####################################################################################################################
    #
    ####################################################################################################################
    def item_info(self, queue_id:int, **kwargs) -> Response:
        return  self.get(self.item_info_extension.format(queue_id), **kwargs)
