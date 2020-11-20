########################################################################################################################
#
########################################################################################################################
from api.tree.filterlist    import FilterList
from network.communicator   import Communicator
from api.treeapi            import TreeAPI
from requests.models        import Response


########################################################################################################################
#
########################################################################################################################
class BuildAPI(TreeAPI):

    ####################################################################################################################
    #
    ####################################################################################################################
    def __init__(self, url_base:str, communicator:Communicator):
        super().__init__(url_base=url_base, communicator=communicator)

        self.job_extension:str          = '/job/{0}'
        self.info_extension:str         = f'{self.job_extension}/{{1}}{self.format}'
        self.stop_extension:str         = f'{self.job_extension}/{{1}}/stop'
        self.kill_extension:str         = f'{self.job_extension}/{{1}}/kill'
        self.terminate_extension:str    = f'{self.job_extension}/{{1}}/term'

    ####################################################################################################################
    #
    ####################################################################################################################
    def stop(self, job_name:str, build_id:int) -> Response:
        return self.post(self.stop_extension.format(job_name, build_id))

    ####################################################################################################################
    #
    ####################################################################################################################
    def kill(self, job_name:str, build_id:int) -> Response:
        return self.post(self.kill_extension.format(job_name, build_id))

    ####################################################################################################################
    #
    ####################################################################################################################
    def terminate(self, job_name:str, build_id:int) -> Response:
        return self.post(self.terminate_extension.format(job_name, build_id))

    ####################################################################################################################
    #
    ####################################################################################################################
    def info(self, job_name:str, build_id:int, **kwargs) -> Response:
        return self.get(self.info_extension.format(job_name, build_id), **kwargs)
