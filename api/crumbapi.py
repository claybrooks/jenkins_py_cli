########################################################################################################################
#
########################################################################################################################
from api.hostapi            import HostAPI
from requests.models        import Response
from network.communicator   import Communicator
import json

########################################################################################################################
#
########################################################################################################################
class CrumbAPI(HostAPI):

    ####################################################################################################################
    #
    ####################################################################################################################
    def __init__(self, url_base:str, communicator:Communicator):
        super().__init__(url_base=url_base, communicator=communicator)
        self.crumb_extension = f'/crumbIssuer{self.format}'

    ####################################################################################################################
    #
    ####################################################################################################################
    def crumb(self) -> tuple[str,str]:
        resp:Response = self.get(self.crumb_extension)

        if resp.status_code != 200:
            return (None, None)

        # unpack crumb data and store
        content = json.loads(resp.content)

        return (content['crumb'], content['crumbRequestField'])
