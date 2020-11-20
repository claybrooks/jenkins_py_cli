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
class JobAPI(TreeAPI):

    ####################################################################################################################
    #
    ####################################################################################################################
    def __init__(self, url_base:str, communicator:Communicator):
        super().__init__(url_base=url_base, communicator=communicator)

        self.parameter_build_extension  = '/job/{}/buildWithParameters'
        self.build_extension            = '/job/{}/build'
        self.info_extension             = f'/job/{{}}{self.format}'

    ####################################################################################################################
    #
    ####################################################################################################################
    def build(self, job_name:str, params:dict[str,str]={}) -> Response:
        if params != {}:
            return self.build_with_parameters(job_name=job_name, params=params)
        else:
            return self.post(self.build_extension.format(job_name))

    ####################################################################################################################
    #
    ####################################################################################################################
    def build_with_parameters(self, job_name:str, params:dict) -> Response:
        return self.post(self.parameter_build_extension.format(job_name), params=params)

    ####################################################################################################################
    #
    ####################################################################################################################
    def info(self, job_name:str, **kwargs) -> Response:
        return self.get(self.info_extension.format(job_name), **kwargs)
