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
    def __init__(self, url_base:str, username:str, password:str=None, api_token:str=None, api_token_file:str=None):

        # Create the communicator
        self.communicator = Communicator(
            username=username,
            password=password,
            api_token=api_token,
            api_token_file=api_token_file
        )

        # create the api
        self.api:JenkinsAPI = JenkinsAPI(
            url_base=url_base,
            communicator=self.communicator,
        )

        # list of jobs that we have
        self.jobs:dict[str, Job] = {}

        # say that we have/have not initialize
        self.initialized = False

        self.job_change_listeners:list[Callable[[Job, bool]]] = []

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

            time.sleep(.25)

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
            for c in self.job_change_listeners:
                c(job, False)
            del self.jobs[job]

        for job in jobs_to_add:
            # add the job to the queue
            self.jobs[job] = Job(
                name=job,
                api=self.api
            )
            for c in self.job_change_listeners:
                c(self.jobs[job], True)

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

    ####################################################################################################################
    #
    ####################################################################################################################
    def register_job_change(self, callback:Callable[[Job, bool], None]):
        self.job_change_listeners.append(callback)

    ####################################################################################################################
    #
    ####################################################################################################################
    def get_user_token(self, user:str):
        resp = self.api.people_api.user_configure(username=user)
        i = 0


########################################################################################################################
#
########################################################################################################################
def main(args=sys.argv[1:]):
    parser = argparse.ArgumentParser()

    parser.add_argument('--server',                     action='store')
    parser.add_argument('--user',                       action='store')

    subparsers = parser.add_subparsers(title="command", dest='command')

    auth_group = parser.add_mutually_exclusive_group(required=True)
    auth_group.add_argument('--password',       action='store')
    auth_group.add_argument('--api-token',      action='store')
    auth_group.add_argument('--api-token-file', action='store')

    job_parser = subparsers.add_parser(name="job")
    user_parser= subparsers.add_parser(name="user")

    job_parser.add_argument('--list',                   action='store_true',    default=False)
    job_parser.add_argument('--list-running',           action='store_true',    default=False)
    job_parser.add_argument('--info',                   action='store',         default=None)
    job_parser.add_argument('--start',                  action='store',         default=None)
    job_parser.add_argument('--stop',                   action='store',         default=None)
    job_parser.add_argument('--param',                  action='append',        default=[])
    job_parser.add_argument('--wait-for-start',         action='store_true',    default=False)
    job_parser.add_argument('--wait-for-completion',    action='store_true',    default=False)

    user_parser.add_argument('--get-api-token', action='store_true', default=False)

    args = parser.parse_args(args)

    jenkins = Jenkins(
        url_base=args.server,
        username=args.user,
        password=args.password,
        api_token=args.api_token,
        api_token_file=args.api_token_file
    )

    while not jenkins.initialized:
        pass

    wait_for_thread_signal = False

    if args.command == 'job':
        if args.list:
            jobs = jenkins.get_jobs()
            print (', '.join(jobs))

        elif args.list_running:
            running_jobs = jenkins.get_running_jobs()
            print (', '.join(running_jobs))

        elif args.info:
            jenkins.job_info(args.job_info)

        elif args.start is not None:
            job = jenkins.start_job_instance(
                args.start,
                job_params_kvp=args.param,
                status_callback=lambda f: print ("hello")
            )

            job.register_status_update(lambda j: print (f"{j.name} was updated: {j.info}"))

            while not job.complete:
                time.sleep(1)

        elif args.stop is not None:
            jenkins.stop_job(args.stop)

        while wait_for_thread_signal:
            pass
    elif args.user:
        if args.get_api_token:
            print (jenkins.get_user_token(args.user))
    jenkins.stop()

########################################################################################################################
#
########################################################################################################################
if __name__ == '__main__':
    main()
