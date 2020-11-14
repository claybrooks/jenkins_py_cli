########################################################################################################################
#
########################################################################################################################
from jenkinsurlhelper import JenkinsURLHelper
import  json
import  requests
from    requests.models import HTTPBasicAuth, Response

import logging
LOGGER = logging.getLogger(__file__)

########################################################################################################################
#
########################################################################################################################
class JenkinsCommunicator:

    ####################################################################################################################
    #
    ####################################################################################################################
    def __init__(self, server:str, username:str, password:str):
        self.server     = server
        self.username   = username
        self.password   = password

        self.url_helper = JenkinsURLHelper(url_base=server)

        self.auth:HTTPBasicAuth = HTTPBasicAuth(username=self.username, password=self.password)

        self.session:requests.Session       = requests.Session()

        self.crumb:str                      = None
        self.crumb_request_field:str        = None

        self.start()

    ####################################################################################################################
    #
    ####################################################################################################################
    def __response(self, url, func) -> Response:
        try:
            headers = {
                'Accept': 'application/json'
            }

            if None not in [self.crumb, self.crumb_request_field]:
                headers[self.crumb_request_field] = self.crumb

            resp:Response = func(
                url=url,
                auth=self.auth,
                headers=headers
            )

            return resp

        except Exception as e:
            LOGGER.warning(e)
            return None

    ####################################################################################################################
    #
    ####################################################################################################################
    @property
    def valid(self) -> bool:
        return None not in [self.crumb, self.crumb_request_field]

    ####################################################################################################################
    #
    ####################################################################################################################
    def start(self) -> bool:

        resp:Response = self.get(self.url_helper.base)

        if resp.status_code == 200:
            self.update_crumb()

        return resp.status_code == 200

    ####################################################################################################################
    #
    ####################################################################################################################
    def stop(self) -> bool:
        return True

    ####################################################################################################################
    #
    ####################################################################################################################
    def update_crumb(self):
        resp:Response = self.get(self.url_helper.crumb)
        content = json.loads(resp.content)
        self.crumb = content['crumb']
        self.crumb_request_field = content['crumbRequestField']
        LOGGER.debug(f'Got Crumb Info: {self.crumb_request_field}:{self.crumb}')

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