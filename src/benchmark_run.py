"""
This module replaces `run.sh`.
"""

from multiprocessing import Pool
from uuid import uuid4
import logging

from src.task_runner import TaskRunner

log = logging.getLogger(__name__)

class InvalidRunConfigurationException(Exception):
    pass

class TopologyConfiguration:
    def _full_options(self, options_dict):
        return [self.jvm["path"], "-jar", self.jar] + self.jvm["options"] + options_dict["options"]

    @staticmethod
    def from_dict(props):
        if isinstance(props, TopologyConfiguration):
            return props
        elif isinstance(props, dict):
            return TopologyConfiguration(**props)
        else:
            raise Exception

    def __init__(self, controller=None, backends=None, injectors=None, jvm=None, jar=None):
        if None in [backends, injectors, jvm, jar] or not isinstance(jar, str):
            raise Exception

        self.jar = jar

        if isinstance(jvm, str):
            self.jvm = {
                    "path": jvm,
                    "options": []
                    }
        elif isinstance(jvm, list):
            self.jvm = {
                    "path": jvm[0],
                    "options": jvm[1:],
                    }
        elif isinstance(jvm, dict):
            self.jvm = jvm
        else:
            raise Exception

        if controller is None:
            self.controller = {
                "count": 1,
                "options": ["-m", "MULTICONTROLLER"],
                }
        elif isinstance(controller, dict):
            self.controller = controller
        elif isinstance(controller, list):
            self.controller = {
                    "count": 1,
                    "options": controller,
                }

        if isinstance(backends, int):
            self.backends = {
                "count": backends,
                "options": ["-m", "BACKEND"],
                }
        elif isinstance(backends, dict):
            self.backends = backends
        else:
            raise Exception

        if isinstance(injectors, int):
            self.injectors = {
                    "count": injectors,
                    "options": ["-m", "TXINJECTOR"],
            }
        elif isinstance(injectors, dict):
            self.injectors = injectors
        else:
            raise Exception

    def controller_run_args(self):
        return self._full_options(self.controller)

    def backend_run_args(self):
        return self._full_options(self.backends)

    def injector_run_args(self):
        return self._full_options(self.injectors)

def do(task):
    """
    Runs a given task synchronously.
    """
    log.debug("starting task {}".format(task))
    task.run()
    log.debug("finished task {}".format(task))

class SpecJBBRun:
    """
    Does a run!
    """

    def __init__(self, 
            args=None,
            annotations=None,
            types=None,
            translations=None,
            default_props=None,
            props=None):
        if types is None or props is None or args is None:
            raise InvalidRunConfigurationException

        self.args = args
        self.types = types
        self.translations = translations
        self.props = TopologyConfiguration.from_dict(props)

        self.run_id = uuid4()
        self.log = logging.LoggerAdapter(log, { 'run_id': self.run_id })

    def _generate_tasks(self):
        self.log.info(
                "generating {} groups, each with {} transaction injectors"
                .format(self.props.backends["count"], self.props.injectors["count"]))

        for _ in range(self.props.backends["count"]):
            group_id = uuid4()
            backend_jvm_id = uuid4()
            self.log.debug("constructing group {}".format(group_id))
            yield TaskRunner(*self.props.backend_run_args(),
                '-G={}'.format(group_id),
                '-J={}'.format(backend_jvm_id))

            self.log.debug("constructing injectors for group {}".format(group_id))

            for _ in range(self.props.injectors["count"]):
                ti_jvm_id = uuid4()
                self.log.debug("preparing injector in group {} with jvmid={}".format(group_id, ti_jvm_id))
                yield TaskRunner(*self.props.injector_run_args(),
                    '-G={}'.format(group_id),
                    '-J={}'.format(ti_jvm_id))

    def run(self):
        # setup jvms
        # we first need to setup the controller
        c = TaskRunner(*self.props.controller_run_args())

        tasks = [c] + [ task for task in self._generate_tasks() ]
        pool = Pool(processes=len(tasks))

        # run benchmark
        self.log.info("begin benchmark")

        pool.map(do, tasks)

        # TODO: collect results

    def dump(self, level=logging.DEBUG):
        """
        Dumps info about this currently configured run.
        """

        self.log.log(level, vars(self))
