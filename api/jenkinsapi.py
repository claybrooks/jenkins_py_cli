########################################################################################################################
#
########################################################################################################################
from api.hostapi import HostAPI
from api.jobapi import JobAPI
from .buildapi  import BuildAPI
from .crumbapi  import CrumbAPI
from .queueapi  import QueueAPI

from network.communicator   import Communicator


########################################################################################################################
#
########################################################################################################################
class JenkinsAPI:

    ####################################################################################################################
    #
    ####################################################################################################################
    def __init__(self,url_base:str,communicator:Communicator):

        self.host_api:HostAPI   = HostAPI(  url_base=url_base, communicator=communicator)
        self.build_api:BuildAPI = BuildAPI( url_base=url_base, communicator=communicator)
        self.crumb_api:CrumbAPI = CrumbAPI( url_base=url_base, communicator=communicator)
        self.job_api:JobAPI     = JobAPI(   url_base=url_base, communicator=communicator)
        self.queue_api:QueueAPI = QueueAPI( url_base=url_base, communicator=communicator)
