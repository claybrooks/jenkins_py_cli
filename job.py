########################################################################################################################
#
########################################################################################################################
from    tree.filterlist     import FilterList
from    tree.filternode     import FilterNode
from    jenkinsexceptions   import InvalidResponse, JobInstanceNotFound
from    jenkinsqueue        import JenkinsQueue
from    jobinstance         import JobInstance
from    jenkinscommunicator import JenkinsCommunicator
from    typing              import Callable
from    requests.models     import Response
import  logging
LOGGER = logging.getLogger(__file__)


########################################################################################################################
#
########################################################################################################################
class Job:

    ####################################################################################################################
    #
    ####################################################################################################################
    def __init__(self, name:str, communicator:JenkinsCommunicator, queue:JenkinsQueue, max_history=100):
        self.communicator   = communicator
        self.queue          = queue
        self.name           = name
        self.urls           = self.communicator.url_helper
        self.max_history    = max_history

        self.instances:list[JobInstance] = []

        self.build_status_listeners:dict[tuple(str, int), Callable[[int, str], None]] = {}
        self.queue_status_listeners:dict[tuple(str, int), Callable[[int, str], None]] = {}

        self.update(check_active_builds=False)

    ####################################################################################################################
    #
    ####################################################################################################################
    def from_response(self, response:Response):

        if response.status_code != 200:
            raise InvalidResponse(f"Job {self.name} given an invalid response to parse")

        data = response.json()

        # builds we received from network
        for build in data['builds']:
            number = build['number']
            queue_id = build['queueId']

            inst = self.find_instance(build_id=number, queue_id=queue_id)
            if not inst:
                inst = JobInstance(
                    communicator=self.communicator,
                    job_name=self.name,
                    build_id=number
                )
                self.instances.append(inst)
            inst.update_from_json(build)

    ####################################################################################################################
    #
    ####################################################################################################################
    def update(self, check_active_builds=True):
        builds_filter = FilterList()\
            .with_filter('builds')\
                .with_lower_bound(0)\
                .with_upper_bound(self.max_history)\
                .add_child('building')\
                .add_child('duration')\
                .add_child('result')\
                .add_child('number')\
                .add_child('queueId')

        self.from_response(self.communicator.get(self.urls.job_build_info(self.name, builds_filter)))

    ####################################################################################################################
    #
    ####################################################################################################################
    def has_active_builds(self) -> bool:
        return any(x for x in self.instances if not x.complete)

    ####################################################################################################################
    #
    ####################################################################################################################
    def spawn_instance(self, params:dict={}, status_callback:Callable[[JobInstance], None]=None) -> JobInstance:

        # request to start the job
        resp:Response = self.communicator.post(self.urls.start_job(self.name, params=params))

        # we failed
        if resp.status_code != 201:
            LOGGER.warning('Could not start job: ' + self.name + '. Reason: ' + resp.content)
            return None

        # get the queue id
        queue_id:int = int(resp.headers['Location'].split('/')[-2])

        # create the job_instance object
        job_instance = JobInstance(
            communicator=self.communicator,
            job_name=self.name,
            queue_id=queue_id
        )

        # store it
        self.instances.append(job_instance)

        return job_instance

    ####################################################################################################################
    #
    ####################################################################################################################
    def has_instance(self, build_id:int=None, queue_id:int=None) -> bool:
        instance:JobInstance = None

        if build_id is not None:
            instance = any(x for x in self.instances if x.build_id == build_id)

        if instance is not None:
            return True
        if instance is None and queue_id is not None:
            instance = any(x for x in self.instances if x.queue_id == queue_id)

        return instance is not None

    ####################################################################################################################
    #
    ####################################################################################################################
    def find_instance(self, build_id:int=None, queue_id:int=None) -> JobInstance:
        instance:JobInstance = None

        if build_id is not None:
            instance = next((x for x in self.instances if x.build_id == build_id), instance)

        if instance is None and queue_id is not None:
            instance = next((x for x in self.instances if x.queue_id == queue_id), instance)

        return instance
