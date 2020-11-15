########################################################################################################################
#
########################################################################################################################
from api.jenkinsapi import JenkinsAPI
from    api.tree.filterlist     import FilterList
from    typing                  import Callable
from    exceptions              import JobWaiting, InvalidResponse, JobInstanceConstructException, JobInstanceNotBuilding
from    requests.models         import Response
from    network.communicator    import Communicator
import   logging

LOGGER = logging.getLogger(__file__)

########################################################################################################################
# User can override this class to add custom filters
########################################################################################################################
class JobInstance:

    ####################################################################################################################
    #
    ####################################################################################################################
    def __init__(self, api:JenkinsAPI, job_name:str, build_id:int=None, queue_id=None):
        if build_id is None and queue_id is None:
            raise JobInstanceConstructException("One of build_id and queue_id must be specified")

        self.api        = api

        self.build_id   = build_id
        self.queue_id   = queue_id
        self.name       = job_name
        self.complete   = False

        self.info = {
            'build_id': build_id,
            'queue_id': queue_id,
            'name':     job_name,
            'complete': self.complete,
        }

        self.update_listeners:list[Callable[[JobInstance], None]] = []

        # minimal amount of data needed to follow the build movement from the queue to actually building
        self.queue_filter = FilterList()\
            .with_filter('id')\
            .with_filter('why')\
            .begin_filter('executable')\
                .with_filter('number')\
                .with_filter('url')\
                .end()

        # minimal amount of necessary data to display information about a build.  Users can add to this list as they
        # see fit
        self.build_filters = FilterList()\
            .with_filter('building')\
            .with_filter('duration')\
            .with_filter('number')\
            .with_filter('queueId')\
            .with_filter('result')

    ####################################################################################################################
    #
    ####################################################################################################################
    def get_build_property(self, key) -> str:

        # users can't query build_id info until the build_id has been given to us
        if self.build_id is None:
            raise JobWaiting("Job has not started building yet, can't query by build_id")

        if key in self.info:
            return self.info[key]

        # the key isn't in the info dict, try to retrieve from the server
        custom_filter = FilterList()\
            .with_filter(key)

        resp = self.api.build_api.info(build_id=self.build_id, filter=custom_filter)

        if resp.status_code != 200:
            LOGGER.warning(f"Key:{key} not in current build info and not retrievable from server.")
            return None

        self.info[key] = resp.json()[key]

        return self.info.get(key, None)

    ####################################################################################################################
    #
    ####################################################################################################################
    def stop(self):
        if not self.complete:
            self.api.build_api.stop(job_name=self.name, build_id=self.build_id)

    ####################################################################################################################
    #
    ####################################################################################################################
    def terminate(self):
        if not self.complete:
            self.api.build_api.terminate(job_name=self.name, build_id=self.build_id)

    ####################################################################################################################
    #
    ####################################################################################################################
    def kill(self):
        if not self.complete:
            self.api.build_api.kill(job_name=self.name, build_id=self.build_id)

    ####################################################################################################################
    #
    ####################################################################################################################
    def update_from_json(self, json:dict):
        self.complete   = not json['building']
        self.duration   = json['duration']
        self.result     = json['result']

    ####################################################################################################################
    #
    ####################################################################################################################
    def update(self):
        # we are not complete
        if self.complete:
            return

        # if we do not have a build id, then we are in the queue, get info
        if not self.build_id:
            try:
                self.from_queue_response(
                    self.api.queue_api.item_info(queue_id=self.queue_id, filter=self.queue_filter)
                )
            except InvalidResponse:
                pass
        # we have a build id, just query the build status
        else:
            try:
                self.from_build_response(
                    self.api.build_api.info(job_name=self.name, build_id=self.build_id, filter=self.build_filters)
                )
            except InvalidResponse:
                pass

    ####################################################################################################################
    #
    ####################################################################################################################
    def from_build_response(self, response:Response):
        if response.status_code != 200:
            raise InvalidResponse("Invalid response")

        data = response.json()

        self.complete       = not data['building']
        self.duration_in_ms = data['duration']
        self.result         = data['result']

    ####################################################################################################################
    #
    ####################################################################################################################
    def from_queue_response(self, response:Response):
        if response.status_code != 200:
            raise InvalidResponse("Invalid response")

        data = response.json()

        # this thing is no longer in the queue
        if 'why' in data and data['why'] is None and 'executable' in data:
            self.build_id = int(data['executable']['number'])
            self.in_queue = False

    ####################################################################################################################
    #
    ####################################################################################################################
    def register_status_update(self, status_callback:Callable):
        self.update_listeners.append(status_callback)
