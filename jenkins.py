########################################################################################################################
#
########################################################################################################################

from api.tree.filterlist import FilterList
from    api.jenkinsapi          import JenkinsAPI

import  argparse
from    exceptions              import InvalidResponse
from    jobinstance             import JobInstance
from    network.communicator    import Communicator
from    job                     import Job

from    requests.models         import Response
import  sys
from    threading               import Thread
import  time
from    typing                  import Callable

import  logging
logging.basicConfig()
logging.root.setLevel(logging.INFO)
LOGGER = logging.getLogger(__file__)
LOGGER.setLevel(logging.INFO)


########################################################################################################################
#
########################################################################################################################
class JobNotFound(Exception):
    def __init__(*args, **kwargs):
        super().__init__(*args, **kwargs)


########################################################################################################################
#
########################################################################################################################
class Jenkins:

    ####################################################################################################################
    #
    ####################################################################################################################
    def __init__(self, url_base:str, username:str, password:str):

        # Create the communicator
        self.communicator = Communicator(username=username, password=password)

        # create the api
        self.api:JenkinsAPI = JenkinsAPI(
            url_base=url_base,
            communicator=self.communicator,
        )

        # list of jobs that we have
        self.jobs:dict[str, Job] = {}

        # say that we have/have not initialize
        self.initialized = False

        # our status thread
        self.status_thread:Thread       = Thread(target=self.__status_thread_entry, name='StatusThread')
        self.status_thread_exit:bool    = False
        self.status_thread.start()

    ####################################################################################################################
    #
    ####################################################################################################################
    def __status_thread_entry(self):

        # set the crumbs
        self.communicator.set_crumbs(*self.api.crumb_api.crumb())

        while not self.status_thread_exit:

            # get jobs from the server and create as necessary
            try:
                self.__jobs_from_response(
                    response=self.api.host_api.info(filter=FilterList().begin_filter('jobs').with_filter('name'))
                )
            except InvalidResponse:
                pass

            for job in self.jobs.values():
                job.update()

            if not self.initialized:
                self.initialized = True

            time.sleep(1)

    ####################################################################################################################
    #
    ####################################################################################################################
    def __jobs_from_response(self, response:Response):
        if response.status_code != 200:
            raise InvalidResponse("Invalid Response")

        data = response.json()

        # get all of the job names that were given to us
        job_names = [x['name'] for x in data['jobs']]

        # figure out what to add and remove from jobs dict
        jobs_to_add     = list(set(job_names).difference(set(self.jobs.keys())))
        jobs_to_remove  = list(set(self.jobs.keys()).difference(set(job_names)))

        for job in jobs_to_remove:
            del self.jobs[job]

        for job in jobs_to_add:
            # add the job to the queue
            self.jobs[job] = Job(
                name=job,
                api=self.api
            )

    ####################################################################################################################
    #
    ####################################################################################################################
    def get_job(self, job_name:str) -> Job:

        # we already have this job, just return it
        if job_name in self.jobs:
            return self.jobs[job_name]

        # create an instance
        job:Job = Job(
            name=job_name,
            api=self.api
        )

        # add to the jobs dict
        self.jobs[job_name] = job

        return job

    ####################################################################################################################
    #
    ####################################################################################################################
    def stop(self):
        if self.status_thread:
            self.status_thread_exit = True
            self.status_thread.join()

    ####################################################################################################################
    #
    ####################################################################################################################
    def start_job_instance(
        self,
        job_name:str,
        job_params_kvp:list=[],
        job_params_dict:dict={},
        status_callback:Callable[[JobInstance], None]=None
    ) -> JobInstance:

        # Copy of the passed in dict so we don't modify the source
        params = dict(job_params_dict)

        # we were also given key value pair
        if len(job_params_kvp) > 0:
            # split on '=' and push into params
            for param in job_params_kvp:
                key,value = param.split('=')
                params[key] = value

        # get the job
        job:Job = self.get_job(job_name)

        # spawn an instance of the job
        return job.spawn_instance(params, status_callback)

    ####################################################################################################################
    #
    ####################################################################################################################
    def job_list(self) -> list[str]:
        return [x.name for x in self.jobs]


########################################################################################################################
#
########################################################################################################################
def main(args=sys.argv[1:]):
    parser = argparse.ArgumentParser()

    parser.add_argument('--server',                     action='store')
    parser.add_argument('--user',                       action='store')
    parser.add_argument('--password',                   action='store')

    parser.add_argument('--list-jobs',                  action='store_true',    default=False)
    parser.add_argument('--list-running-jobs',          action='store_true',    default=False)
    parser.add_argument('--job-info',                   action='store',         default=None)
    parser.add_argument('--start-job',                  action='store',         default=None)
    parser.add_argument('--stop-job',                   action='store',         default=None)
    parser.add_argument('--job-param',                  action='append',        default=[])
    parser.add_argument('--wait-for-job-start',         action='store_true',    default=False)
    parser.add_argument('--wait-for-job-completion',    action='store_true',    default=False)

    args = parser.parse_args(args)

    jenkins = Jenkins(
        url_base=args.server,
        username=args.user,
        password=args.password
    )

    while not jenkins.initialized:
        pass

    wait_for_thread_signal = False

    if args.list_jobs:
        jobs = jenkins.get_jobs()
        print (', '.join(jobs))

    elif args.list_running_jobs:
        running_jobs = jenkins.get_running_jobs()
        print (', '.join(running_jobs))

    elif args.job_info:
        jenkins.job_info(args.job_info)

    elif args.start_job is not None:
        job = jenkins.start_job_instance(
            args.start_job,
            job_params_kvp=args.job_param,
            status_callback=lambda f: print ("hello")
        )

        while not job.complete:
            print ("Waiting for job completeion")
            time.sleep(1)

    elif args.stop_job is not None:
        jenkins.stop_job(args.stop_job)

    while wait_for_thread_signal:
        pass
    jenkins.stop()

########################################################################################################################
#
########################################################################################################################
if __name__ == '__main__':
    main()
