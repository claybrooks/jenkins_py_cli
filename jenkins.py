########################################################################################################################
#
########################################################################################################################
import  argparse
import  json
from logging import log

from    requests.adapters import Response
from    requests.models import HTTPBasicAuth
from    typing import Callable
import  requests
import  sys
from    threading import Thread
import  time

import  logging
logging.basicConfig()
logging.root.setLevel(logging.INFO)
LOGGER = logging.getLogger(__file__)
LOGGER.setLevel(logging.INFO)


########################################################################################################################
#
########################################################################################################################
class Jenkins:

    ####################################################################################################################
    #
    ####################################################################################################################
    def __init__(self, server:str, user:str, password:str):
        self.server:str                     = server
        self.user:str                       = user
        self.password:str                   = password

        self.session:requests.Session       = requests.Session()

        self.crumb:str                      = None
        self.crumb_request_field:str        = None

        self.auth:HTTPBasicAuth             = HTTPBasicAuth(username=self.user, password=self.password)

        self.build_status:dict[tuple(str, int), str]    = {}
        self.queue_status:dict[tuple(str, int), str]                = {}

        self.build_status_listeners:dict[tuple(str, int), Callable[[int, str], None]] = {}
        self.queue_status_listeners:dict[tuple(str, int), Callable[[int, str], None]] = {}

        self.status_thread:Thread           = None
        self.status_thread_exit:bool        = False

        self.check_server()

    ####################################################################################################################
    #
    ####################################################################################################################
    def __response(self, url, func):
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
    def __get_response(self, url, include_crumb=False):
        LOGGER.debug('Getting: ' + url)
        return self.__response(url, self.session.get)

    ####################################################################################################################
    #
    ####################################################################################################################
    def __post_response(self, url, include_crumb=False):
        LOGGER.debug('Posting: ' + url)
        return self.__response(url, self.session.post)

    ####################################################################################################################
    #
    ####################################################################################################################
    def __get_crumb(self):
        resp:Response = self.__get_response(self.url_crumb)
        content = json.loads(resp.content)
        self.crumb = content['crumb']
        self.crumb_request_field = content['crumbRequestField']
        LOGGER.debug(f'Got Crumb Info: {self.crumb_request_field}:{self.crumb}')

    ####################################################################################################################
    #
    ####################################################################################################################
    def __add_listener(self, storage:dict[int, list], id:int, callback:Callable):
        if id not in storage:
            storage[id] = []

        storage[id].append(callback)

        if self.status_thread is None:
            self.status_thread_exit = False
            self.status_thread = Thread(target=self.__status_thread_entry, name='StatusThread')
            self.status_thread.start()

    ####################################################################################################################
    #
    ####################################################################################################################
    def __add_build_status_listener(self, id, callback:Callable[[int, str], None]):
        self.__add_listener(self.build_status_listeners, id, callback)

    ####################################################################################################################
    #
    ####################################################################################################################
    def __add_queue_status_listener(self, id, callback:Callable[[int, str], None]):
        self.__add_listener(self.queue_status_listeners, id, callback)

    ####################################################################################################################
    #
    ####################################################################################################################
    def __status_thread_entry(self):

        while not self.status_thread_exit:

            self.__update_status(self.__update_queue_status, self.queue_status_listeners)
            self.__update_status(self.__update_build_status, self.build_status_listeners)

            time.sleep(1)

    ####################################################################################################################
    #
    ####################################################################################################################
    def __update_status(self, status_func, listener_dict):

        # ids to remove
        remove = []

        for id,listeners in listener_dict.items():

            should_remove, should_trigger, data_notification = status_func(id)

            if should_remove:
                remove.append(id)

            if should_trigger:
                # notify everybody
                for l in listeners:
                    l(*data_notification)

        # there are some queue id's that need to be removed, remove them
        for r in remove:
            del listener_dict[r]

    ####################################################################################################################
    #
    ####################################################################################################################
    def __update_queue_status(self, id):
        # unpack the id
        job_name,queue_id = id

        # get the status and possible next build id
        status, build_id = self.get_queue_status(queue_id=queue_id)

        # should we remove this id from being checked?
        should_remove = status == "REMOVED"

        # should we notify listeners of new data?
        should_trigger = id not in self.queue_status or self.queue_status[id] != status

        # store the current status
        self.queue_status[id] = status

        # data that needs to be notified if any
        data_notification = (job_name, queue_id, status, build_id)

        return should_remove, should_trigger, data_notification

    ####################################################################################################################
    #
    ####################################################################################################################
    def __update_build_status(self, id):
        # unpack the id
        job_name, build_id = id

        building, status = self.get_build_status(job_name, build_id)

        # this thing is no longer in the queue
        should_remove = not building

        should_trigger = id not in self.build_status or self.build_status[id] != status

        # store the current status
        self.build_status[id] = status

        data_notification = (job_name, build_id, status)

        return should_remove, should_trigger, data_notification

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
    @property
    def server_valid(self) -> bool:
        return None not in [self.crumb, self.crumb_request_field]

    ####################################################################################################################
    #
    ####################################################################################################################
    @property
    def url_base(self) -> str:
        return f'{self.server}'

    ####################################################################################################################
    #
    ####################################################################################################################
    @property
    def url_crumb(self) -> str:
        return f'{self.url_base}/crumbIssuer/api/json'

    ####################################################################################################################
    #
    ####################################################################################################################
    def url_job_config(self, job_name:str) -> str:
        return f'{self.url_base}/job/{job_name}/config.xml'

    ####################################################################################################################
    #
    ####################################################################################################################
    def url_start_job(self, job_name:str, params:dict={}) -> str:
        url = f'{self.url_base}/job/{job_name}/'

        if params != {}:
            url = url + 'buildWithParameters?' + '&'.join([k+'='+v for k,v in params.items()])
        else:
            url = url + '/build'

        return url

    ####################################################################################################################
    #
    ####################################################################################################################
    def url_queue_info(self, queue_id:str=None, partial_queue_url:str=None) -> str:
        if partial_queue_url is None:
            partial_queue_url = f'{self.url_base}/queue/item/{queue_id}'

        return partial_queue_url + '/api/json'

    ####################################################################################################################
    #
    ####################################################################################################################
    def url_build_base(self, job_name:str, build_id:int) -> str:
        return f'{self.url_base}/job/{job_name}/{build_id}'

    ####################################################################################################################
    #
    ####################################################################################################################
    def url_build_info(self, job_name:str, build_id:int) -> str:
        return f"{self.url_build_base(job_name, build_id)}/api/json"

    ####################################################################################################################
    #
    ####################################################################################################################
    def url_control_job(self, job_name:str, build_id:int, control:str) -> str:
        return f'{self.url_build_base(job_name, build_id)}/{control}'

    ####################################################################################################################
    #
    ####################################################################################################################
    def url_stop_job(self, job_name:str, build_id:int) -> str:
        return self.url_control_job(job_name, build_id, 'stop')

    ####################################################################################################################
    #
    ####################################################################################################################
    def url_terminate_job(self, job_name:str, build_id:int) -> str:
        return self.url_control_job(job_name, build_id, 'term')

    ####################################################################################################################
    #
    ####################################################################################################################
    def url_kill_job(self, job_name:str, build_id:int) -> str:
        return self.url_control_job(job_name, build_id, 'kill')

    ####################################################################################################################
    #
    ####################################################################################################################
    @property
    def url_tree(self) -> str:
        return f'{self.url_base}/api/json/tree'

    ####################################################################################################################
    #
    ####################################################################################################################
    @property
    def authorization_string(self) -> str:
        return f'api-key {self.api_key}'

    ####################################################################################################################
    #
    ####################################################################################################################
    def check_server(self) -> bool:
        resp:Response = self.__get_response(self.url_base)

        if resp.status_code == 200:
            self.__get_crumb()

        return resp.status_code == 200

    ####################################################################################################################
    #
    ####################################################################################################################
    def register_build_status(self, job_name:str, job_id:int, callback:Callable[[str, dict], None]) -> None:
        self.__add_build_status_listener((job_name, job_id), callback)

    ####################################################################################################################
    #
    ####################################################################################################################
    def register_queue_status(self, queue_id:int, callback:Callable[[str, dict], None]) -> None:
        self.__add_queue_status_listener(queue_id, callback)

    ####################################################################################################################
    #
    ####################################################################################################################
    def job_info(self, job_id:str) -> dict:
        resp:Response = self.__post_response(self.url_job_config(job_id))
        if resp.status_code != 200:
            LOGGER.warning("Could not retrieve job: " + resp.content)
        else:
            LOGGER.info(resp.content)

    ####################################################################################################################
    #
    ####################################################################################################################
    def get_jobs(self) -> list[str]:
        resp:Response = self.__get_response(f'{self.url_tree}')
        jobs = []
        for job in resp.json()['jobs']:
            jobs.append(job['name'])

        return jobs

    ####################################################################################################################
    #
    ####################################################################################################################
    def get_running_jobs(self) -> list[str]:
        resp:Response = self.__get_response(f'{self.url_tree}')
        jobs = []
        for job in resp.json()['jobs']:
            if job['color'].endswith('_anime'):
                jobs.append(job['name'])

        return jobs

    ####################################################################################################################
    #
    ####################################################################################################################
    def get_running_job_ids(self, job_name:str) -> list[str]:
        resp:Response = self.__get_response(f'{self.url_tree}')
        jobs = []
        for job in resp.json()['jobs']:
            if job['color'].endswith('_anime'):
                jobs.append(job['name'])

        return jobs

    ####################################################################################################################
    #
    ####################################################################################################################
    def start_job(
        self,
        job_name:str,
        job_params_kvp:list=[],
        job_params_dict:dict={},
        queue_status:Callable[[int, str], None]=None
    ) -> bool:

        # Copy of the passed in dict so we don't modify the source
        params = dict(job_params_dict)

        # we were also given key value pair
        if len(job_params_kvp) > 0:
            # split on '=' and push into params
            for param in job_params_kvp:
                key,value = param.split('=')
                params[key] = value

        # start the job
        resp:Response = self.__post_response(self.url_start_job(job_name, params=params), include_crumb=True)

        if resp.status_code != 201:
            LOGGER.warning('Could not start job: ' + job_name + '. Reason: ' + resp.content)
            return -1

        if queue_status is not None:
            id:int = resp.headers['Location'].split('/')[-2]
            self.register_queue_status((job_name, id), queue_status)

        return True

    ####################################################################################################################
    #
    ####################################################################################################################
    def stop_job(self, job_name:str, build_id:int) -> bool:
        resp:Response = self.__post_response(self.url_stop_job(job_name, build_id))
        return resp.status_code == 200

    ####################################################################################################################
    #
    ####################################################################################################################
    def get_build_status(self, job_name:str, build_id:int) -> str:

        resp:Response = self.__get_response(self.url_build_info(job_name=job_name, build_id=build_id))
        reason = resp.json()

        building = reason['building']

        if building:
            status = "BUILDING"
        else:
            status = reason['result']

        return building, status

    ####################################################################################################################
    #
    ####################################################################################################################
    def get_queue_status(self, queue_id:int) -> tuple[str, int]:

        # get the queue info
        resp:Response = self.__get_response(self.url_queue_info(queue_id=queue_id))

        if resp.status_code != 200:
            LOGGER.warning(f"Failed to fetch queue status for {queue_id} with error {resp.status_code}.  Reason:{resp.reason}")
            return None

        reason = resp.json()

        # this thing is no longer in the queue
        if reason['why'] is None and 'executable' in reason:
            status = "REMOVED"
            build_id = int(reason['executable']['number'])
        # it's still waiting in the queue
        else:
            status = 'WAITING'
            build_id = None

        return (status, build_id)

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
        server=args.server,
        user=args.user,
        password=args.password
    )

    if not jenkins.check_server():
        LOGGER.warning('Failed to log in')
        return -1
    else:
        LOGGER.info('Logged In')

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

        callback = None
        if args.wait_for_job_start or args.wait_for_job_completion:

            wait_for_thread_signal = True

            def build_status_print(job_name:str, build_id:int, status:str):
                nonlocal wait_for_thread_signal

                print (f"In Build: {job_name}/{build_id}={status}")

                if status in ["SUCCESS", "FAILURE"]:
                    wait_for_thread_signal = False

            def queue_status_print(job_name:str, queue_id:int, status:str, build_id:int):
                nonlocal wait_for_thread_signal

                print (f"In Queue: {job_name}/{queue_id}={status}")
                if status == 'REMOVED':
                    print (f"In Build: {job_name}/{build_id}")
                    if args.wait_for_job_completion:
                        jenkins.register_build_status(job_name, build_id, build_status_print)
                    else:
                        wait_for_thread_signal = False

            callback = queue_status_print

        jenkins.start_job(
            args.start_job,
            job_params_kvp=args.job_param,
            queue_status=callback
        )

    elif args.stop_job is not None:
        jenkins.stop_job(args.stop_job)

    if wait_for_thread_signal:
        while wait_for_thread_signal:
            pass
        jenkins.stop()

########################################################################################################################
#
########################################################################################################################
if __name__ == '__main__':
    main()
