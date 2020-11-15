########################################################################################################################
#
########################################################################################################################
from logging import Filter
from    tree.filterlist     import FilterList
from    tree.filternode     import FilterNode
from    typing              import Callable
from    jenkinsexceptions   import InvalidResponse, JobInstanceConstructException, JobInstanceNotBuilding
from    requests.models     import Response
from    jenkinscommunicator import JenkinsCommunicator
import  requests

########################################################################################################################
#
########################################################################################################################
class JobInstance:

    ####################################################################################################################
    #
    ####################################################################################################################
    def __init__(self, communicator:JenkinsCommunicator, job_name:str, build_id:int=None, queue_id=None):
        if build_id is None and queue_id is None:
            raise JobInstanceConstructException("One of build_id and queue_id must be specified")

        self.communicator   = communicator
        self.name           = job_name
        self.build_id       = build_id
        self.queue_id       = queue_id

        self.urls           = self.communicator.url_helper

        self.complete       = False
        self.in_queue       = False
        self.result         = None

        self.duration_in_ms = None

        self.update_listeners:list[Callable[[JobInstance], None]] = []

    ####################################################################################################################
    #
    ####################################################################################################################
    def get_info(self):
        pass

    ####################################################################################################################
    #
    ####################################################################################################################
    def start(self):
        pass

    ####################################################################################################################
    #
    ####################################################################################################################
    def __eliminate(self, method:str):
        if self.complete:
            raise JobInstanceNotBuilding(f"{self.name}/{self.build_id} is already complete")

        self.communicator.post(self.urls.control_job(job_name=self.name, build_id=self.build_id, control=method))

    ####################################################################################################################
    #
    ####################################################################################################################
    def stop(self):
        if not self.complete:
            self.communicator.post(self.urls.stop_job(self.name, self.build_id))

    ####################################################################################################################
    #
    ####################################################################################################################
    def terminate(self):
        if not self.complete:
            self.communicator.post(self.urls.terminate_job(self.name, self.build_id))

    ####################################################################################################################
    #
    ####################################################################################################################
    def kill(self):
        if not self.complete:
            self.communicator.post(self.urls.kill_job(self.name, self.build_id))

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

        try:
            # if we do not have a build id, then we are in the queue, get info
            if not self.build_id:
                filter = FilterList()\
                    .with_filter('id')\
                    .with_filter('why')\
                    .begin_filter('executable')\
                        .with_child('number')\
                        .with_child('url')\
                        .end()

                self.from_queue_response(self.communicator.get(self.urls.queue_item_info(self.queue_id, filters=filter)))
            # we have a build id, just query the build status
            else:
                filter = FilterList()\
                    .with_filter('building')\
                    .with_filter('duration')\
                    .with_filter('number')\
                    .with_filter('queueId')\
                    .with_filter('result')

                self.from_build_response(self.communicator.get(self.urls.build_info(self.name, self.build_id)))
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
        if data['why'] is None and 'executable' in data:
            self.build_id = int(data['executable']['number'])
            self.in_queue = False

    ####################################################################################################################
    #
    ####################################################################################################################
    def register_status_update(self, status_callback:Callable):
        self.update_listeners.append(status_callback)
