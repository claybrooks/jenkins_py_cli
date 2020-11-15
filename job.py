########################################################################################################################
#
########################################################################################################################
from    api.jenkinsapi          import JenkinsAPI
from    api.tree.filterlist     import FilterList
from    exceptions              import InvalidResponse
from    jobinstance             import JobInstance
from    typing                  import Callable
from    requests.models         import Response

import  logging
LOGGER = logging.getLogger(__file__)


########################################################################################################################
#
########################################################################################################################
class Job:

    ####################################################################################################################
    #
    ####################################################################################################################
    def __init__(self, name:str, api:JenkinsAPI, max_history=100):

        self.name           = name
        self.api            = api
        self.max_history    = max_history

        self.instances:list[JobInstance] = []

        self.build_status_listeners:dict[tuple(str, int), Callable[[int, str], None]] = {}
        self.queue_status_listeners:dict[tuple(str, int), Callable[[int, str], None]] = {}

        # This is the minimal set of data for a job to instantiate builds
        self.builds_filter = FilterList()\
            .begin_filter('builds')\
                .with_lower_bound(0)\
                .with_upper_bound(self.max_history)\
                .with_filter('number')\
                .with_filter('queueId')\
                .with_filter('building')\
                .with_filter('duration')\
                .with_filter('result')

        # specify depth of 1 so we can can information about builds on a single get
        self.depth = 0

        #self.update(check_active_builds=False)

    ####################################################################################################################
    #
    ####################################################################################################################
    def from_response(self, response:Response):

        if response.status_code != 200:
            raise InvalidResponse(f"Job {self.name} given an invalid response to parse")

        data = response.json()

        # builds we received from network
        for build in data['builds']:

            # extract the two id's we need to search
            build_id = build['number']
            queue_id = build['queueId']

            # try to get the instances of the build
            inst = self.find_instance(build_id=build_id, queue_id=queue_id)

            # we haven't created this object yet
            if not inst:
                # create the job instance
                inst = JobInstance(
                    job_name=self.name,
                    build_id=build_id,
                    queue_id=queue_id,
                    api=self.api
                )
                inst.update_from_json(build)
                self.instances.append(inst)
            else:
                if not inst.complete:
                    # update the instance
                    inst.update()

    ####################################################################################################################
    #
    ####################################################################################################################
    def update(self):
        self.from_response(self.api.job_api.info(job_name=self.name, filter=self.builds_filter, depth=1))

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
        resp:Response = self.api.job_api.build(self.name, params=params)

        # we failed
        if resp.status_code != 201:
            LOGGER.warning('Could not start job: ' + self.name + '. Reason: ' + resp.content)
            return None

        # get the queue id
        queue_id:int = int(resp.headers['Location'].split('/')[-2])

        # create the job_instance object
        job_instance = JobInstance(
            api=self.api,
            job_name=self.name,
            queue_id=queue_id
        )

        # store it
        self.instances.append(job_instance)

        return job_instance

    ####################################################################################################################
    #
    ####################################################################################################################
    def find_instance(self, build_id:int=None, queue_id:int=None) -> JobInstance:
        return next(
            (x for x in self.instances if (
                (build_id is not None and x.build_id == build_id) or (queue_id is not None and x.queue_id == queue_id))
            ),
            None
        )
