########################################################################################################################
#
########################################################################################################################


########################################################################################################################
#
########################################################################################################################
class JenkinsTreeFilter:

    ####################################################################################################################
    #
    ####################################################################################################################
    def __init__(self, name, parent=None):
        self.name:str                   = name
        self.lower_bound:int            = None
        self.upper_bound:int            = None
        self.all:bool                   = False
        self.parent:JenkinsTreeFilter   = parent

        self.children:list[JenkinsTreeFilter] = []

    ####################################################################################################################
    #
    ####################################################################################################################
    def __str__(self) -> str:
        # if self.all is specified, then just *
        if self.all:
            child_string = '*'
        else:
            # commad delimited list of child __str__ representations
            child_string = ','.join(str(c) for c in self.children)

        # default bound is nothing
        bound = ''

        # user specified both bounds
        if self.lower_bound is not None and self.upper_bound is not None:
            bound = f'{{{self.lower_bound},{self.upper_bound}}}'
        # user specified only lower bound
        elif self.lower_bound is not None:
            bound = f'{{{self.lower_bound},}}'
        # user specified only upper bound
        elif self.upper_bound is not None:
            bound = f',{{{self.upper_bound}}}'

        return f'{self.name}[{child_string}]{bound}'

    ####################################################################################################################
    #
    ####################################################################################################################
    def with_lower_bound(self, lower:int):
        self.lower_bound = lower
        return self

    ####################################################################################################################
    #
    ####################################################################################################################
    def with_upper_bound(self, upper:int):
        self.upper_bound = upper
        return self

    ####################################################################################################################
    #
    ####################################################################################################################
    def with_all(self):
        self.all = True
        return self

    ####################################################################################################################
    #
    ####################################################################################################################
    def with_child(self, name):
        filter = JenkinsTreeFilter(
            name=name,
            parent=self
        )
        self.children.append(filter)
        return filter

    ####################################################################################################################
    #
    ####################################################################################################################
    def add_child(self, name):
        filter = JenkinsTreeFilter(
            name=name,
            parent=self
        ).with_all()
        self.children.append(filter)
        return self

    ####################################################################################################################
    #
    ####################################################################################################################
    def end(self):
        if self.parent:
            return self.parent
        else:
            return self


########################################################################################################################
#
########################################################################################################################
class JenkinsTreeFilterList:

    ####################################################################################################################
    #
    ####################################################################################################################
    def __init__(self):
        self.filters:list[JenkinsTreeFilter] = []

    ####################################################################################################################
    #
    ####################################################################################################################
    def __str__(self) -> str:
        return f"{','.join([str(f) for f in self.filters])}"

    ####################################################################################################################
    #
    ####################################################################################################################
    def with_filer(self, name) -> JenkinsTreeFilter:
        self.add_filter(name)
        return self.filters[-1]

    ####################################################################################################################
    #
    ####################################################################################################################
    def add_filter(self, name):
        self.filters.append(
            JenkinsTreeFilter(name)
        )
        return self

########################################################################################################################
#
########################################################################################################################
class JenkinsURLHelper:

    ####################################################################################################################
    #
    ####################################################################################################################
    def __init__(self, url_base:str):
        self.url_base = url_base

    ####################################################################################################################
    #
    ####################################################################################################################
    @property
    def base(self) -> str:
        return f'{self.url_base}'

    ####################################################################################################################
    #
    ####################################################################################################################
    @property
    def crumb(self) -> str:
        return f'{self.base}/crumbIssuer/api/json'

    ####################################################################################################################
    #
    ####################################################################################################################
    @property
    def tree_base(self) -> str:
        return f'{self.base}/api/json?tree'

    ####################################################################################################################
    #
    ####################################################################################################################
    def job_build_info(self, job_name:str, filters:JenkinsTreeFilterList=None) -> str:
        base = f'{self.base}/job/{job_name}/api/json?depth=1'

        if filters:
            base += (f"&tree={str(filters)}")

        return base

    ####################################################################################################################
    #
    ####################################################################################################################
    def job_info(self, job_name:str) -> str:
        return f'{self.base}/job/{job_name}/api/json'

    ####################################################################################################################
    #
    ####################################################################################################################
    @property
    def base_api(self) -> str:
        return f'{self.base}/api/json'

    ####################################################################################################################
    #
    ####################################################################################################################
    @property
    def queue_info(self) -> str:
        return f'{self.base}/queue/api/json'

    ####################################################################################################################
    #
    ####################################################################################################################
    def queue_item_info(self, queue_id:str=None, partial_queue_url:str=None, filters:JenkinsTreeFilterList=None) -> str:
        url = partial_queue_url
        if url is None:
            url = f'{self.base}/queue/item/{queue_id}'

        url += '/api/json'

        if filters:
            url += f'?tree={str(filters)}'

    ####################################################################################################################
    #
    ####################################################################################################################
    def start_job(self, job_name:str, params:dict) -> str:
        url = f'{self.base}/job/{job_name}/'

        if params != {}:
            url = url + 'buildWithParameters?' + '&'.join([k+'='+v for k,v in params.items()])
        else:
            url = url + '/build'

        return url

    ####################################################################################################################
    #
    ####################################################################################################################
    def build_base(self, job_name:str, build_id:int) -> str:
        return f'{self.base}/job/{job_name}/{build_id}'

    ####################################################################################################################
    #
    ####################################################################################################################
    def build_info(self, job_name:str, build_id:int, filters:JenkinsTreeFilterList=None) -> str:
        base = f"{self.build_base(job_name, build_id)}/api/json"

        if filters is not None:
            base += f'?tree={str(filters)}'

        return base

    ####################################################################################################################
    #
    ####################################################################################################################
    def control_job(self, job_name:str, build_id:int, control:str) -> str:
        return f'{self.build_base(job_name, build_id)}/{control}'

    ####################################################################################################################
    #
    ####################################################################################################################
    def stop_job(self, job_name:str, build_id:int) -> str:
        return self.control_job(job_name, build_id, 'stop')

    ####################################################################################################################
    #
    ####################################################################################################################
    def terminate_job(self, job_name:str, build_id:int) -> str:
        return self.control_job(job_name, build_id, 'term')

    ####################################################################################################################
    #
    ####################################################################################################################
    def kill_job(self, job_name:str, build_id:int) -> str:
        return self.control_job(job_name, build_id, 'kill')
