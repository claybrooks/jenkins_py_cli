########################################################################################################################
#
########################################################################################################################
import  json
import  requests
from    requests.models import HTTPBasicAuth, Response

import  logging
LOGGER = logging.getLogger(__file__)

########################################################################################################################
#
########################################################################################################################
class Communicator:

    ####################################################################################################################
    #
    ####################################################################################################################
    def __init__(self, username:str, password:str):

        # auth
        self.auth:HTTPBasicAuth = HTTPBasicAuth(username=username, password=password)

        # hold the session so our crumbs don't reset
        self.session:requests.Session = requests.Session()

        # data from crumbapi
        self.crumb:str = None
        self.crumb_request_field:str = None

    ####################################################################################################################
    #
    ####################################################################################################################
    def __response(self, url, func) -> Response:
        try:
            # specify we want json, I think this is superceded by supplying /api/json to all url requests, but put
            # here just in case
            headers = {}

            # apply the crumb to the header if we have any
            if None not in [self.crumb, self.crumb_request_field]:
                headers[self.crumb_request_field] = self.crumb

            # get the respnose
            return func(
                url=url,
                auth=self.auth,
                headers=headers
            )

        except Exception as e:
            LOGGER.warning(e)
            return None

    ####################################################################################################################
    #
    ####################################################################################################################
    def set_crumbs(self, crumb:str, crumb_request_field:str):
        self.crumb=crumb
        self.crumb_request_field = crumb_request_field

    ####################################################################################################################
    #
    ####################################################################################################################
    @property
    def valid(self) -> bool:
        return None not in [self.crumb, self.crumb_request_field]

    ####################################################################################################################
    #
    ####################################################################################################################
    def get(self, url) -> Response:
        LOGGER.debug('Getting: ' + url)
        return self.__response(url, self.session.get)

    ####################################################################################################################
    #
    ####################################################################################################################
    def post(self, url) -> Response:
        LOGGER.debug('Posting: ' + url)
        return self.__response(url, self.session.post)
