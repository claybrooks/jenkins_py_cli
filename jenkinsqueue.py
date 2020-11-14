########################################################################################################################
#
########################################################################################################################
from jenkinsexceptions import InvalidResponse
from jenkinscommunicator import JenkinsCommunicator
from requests.models import Response

########################################################################################################################
#
########################################################################################################################
class JenkinsQueue:

    ####################################################################################################################
    #
    ####################################################################################################################
    def __init__(self, communicator:JenkinsCommunicator):
        self.communicator   = communicator
        self.urls           = communicator.url_helper

        self.discoverable_items = []
        self.items = []

    ####################################################################################################################
    #
    ####################################################################################################################
    def update(self):
        try:
            self.from_reponse(self.communicator.get(self.urls.queue_info))
        except InvalidResponse:
            pass

    ####################################################################################################################
    #
    ####################################################################################################################
    def from_reponse(self, response:Response):

        if response.status_code != 200:
            raise InvalidResponse("Invalid Response")

        data = response.json()

        # save off any items in the queue
        self.items = data['items']