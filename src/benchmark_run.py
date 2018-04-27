"""
This module replaces `run.sh`.
"""

from multiprocessing import Pool
from uuid import uuid4
import logging

from src.task_runner import TaskRunner

log = logging.getLogger(__name__)


class InvalidRunConfigurationException(Exception):
    def __init__(self, msg="Run was invalid"):
        self.msg = msg

    def __str__(self):
        return self.msg


def do(task):
    """
    Runs a given task synchronously.
    This needs to be pickled for Pool.map, which is why it's hanging out here.
    """
    log.debug("starting task {}".format(task))
    task.run()
    log.debug("finished task {}".format(task))


class SpecJBBRun:
    """
    Does a run!
    """

    def __init__(self,
                 controller=None,
                 backends=None,
                 injectors=None,
                 java=None,
                 jar=None):
        if None in [java, jar] or not isinstance(jar, str):
            raise InvalidRunConfigurationException

        self.jar = jar
        self.run_id = uuid4()
        self.log = logging.LoggerAdapter(log, {'run_id': self.run_id})

        self.__set_java__(java)
        self.__set_topology__(controller, backends, injectors)

    def __set_java__(self, java):
        """
        Sets the internal java dictionary based on what's passed into __init__.
        """
        if isinstance(java, str):
            self.java = {
                "path": java,
                "options": []
            }
        elif isinstance(java, list):
            self.java = {
                "path": java[0],
                "options": java[1:],
            }
        elif isinstance(java, dict):
            self.java = java
        else:
            raise InvalidRunConfigurationException(
                "'java' was not a string, list, or dictionary")

    def __set_topology__(self, controller, backends, injectors):
        """
        Sets the topology dictionaries based on what's passed into __init__.
        Will also raise exceptions if we don't get what we're expecting.
        """
        if controller is None and backends is None and injectors is None:
            raise InvalidRunConfigurationException("no topology specified")
        if not isinstance(controller, dict):
            raise InvalidRunConfigurationException(
                "'controller' was not a dict")
        if "type" not in controller:
            raise InvalidRunConfigurationException(
                "'type' wasn't specified in 'controller'")

        if controller is None:
            self.controller = {
                "type": "composite",
                "options": [],
                "jvm_opts": [],
            }
        else:
            self.controller = controller

            # TODO: ensure the right SPECjbb run arguments are added to "options"

        if isinstance(backends, int):
            self.backends = {
                "count": backends,
                "type": "backend",
                "options": [],
                "jvm_opts": [],
            }
        elif isinstance(backends, dict):
            self.backends = backends

            # TODO: ensure the right SPECjbb run arguments are added to "options"
        elif backends is None:
            self.backends = {
                "count": 1,
                "type": "backend",
                "options": [],
                "jvm_opts": [],
            }
        else:
            raise InvalidRunConfigurationException(
                "'backends' was not an integer or dict")

        if isinstance(injectors, int):
            self.injectors = {
                "count": injectors,
                "type": "txinjector",
                "options": [],
                "jvm_opts": [],
            }
        elif isinstance(injectors, dict):
            self.injectors = injectors

            # TODO: ensure the right SPECjbb run arguments are added to "options"
        elif injectors is None:
            self.injectors = {
                "count": 1,
                "type": "txinjector",
                "options": [],
                "jvm_opts": [],
            }
        else:
            raise InvalidRunConfigurationException(
                "'injectors' was not an integer or dict")

    def _generate_tasks(self):
        if self.controller["type"] is "composite":
            return

        self.log.info(
            "generating {} groups, each with {} transaction injectors"
                .format(self.backends["count"], self.injectors["count"]))

        for _ in range(self.backends["count"]):
            group_id = uuid4()
            backend_jvm_id = uuid4()
            self.log.debug("constructing group {}".format(group_id))
            yield TaskRunner(*self.backend_run_args(),
                             '-G={}'.format(group_id),
                             '-J={}'.format(backend_jvm_id))

            self.log.debug(
                "constructing injectors for group {}".format(group_id))

            for _ in range(self.injectors["count"]):
                ti_jvm_id = uuid4()
                self.log.debug(
                    "preparing injector in group {} with jvmid={}".format(group_id, ti_jvm_id))
                yield TaskRunner(*self.injector_run_args(),
                                 '-G={}'.format(group_id),
                                 '-J={}'.format(ti_jvm_id))

    def run(self):
        # setup jvms
        # we first need to setup the controller
        c = TaskRunner(*self.controller_run_args())
        self.dump()

        if self.controller["type"] is "composite":
            self.log.info("begin benchmark")
            c.run()
            self.log.info("done")
            return

        c.start()

        tasks = [task for task in self._generate_tasks()]
        pool = Pool(processes=len(tasks))

        self.dump()

        # run benchmark
        self.log.info("begin benchmark")

        pool.map(do, tasks)
        c.stop()
        self.log.info("done")

    def dump(self, level=logging.DEBUG):
        """
        Dumps info about this currently configured run.
        """

        self.log.log(level, vars(self))

    def _full_options(self, options_dict):
        """
        Returns a list of arguments, formatted for the specific JVM invocation.
        """
        self.log.debug("full options being generated from: {}".format(options_dict))

        java = [self.java["path"], "-jar", self.jar] + self.java["options"] + options_dict.get("jvm_opts", [])
        spec = ["-m", options_dict["type"].upper()] + options_dict.get("options", [])

        self.log.debug("java: {}, spec: {}".format(java, spec))

        return java + spec

    def controller_run_args(self):
        return self._full_options(self.controller)

    def backend_run_args(self):
        return self._full_options(self.backends)

    def injector_run_args(self):
        return self._full_options(self.injectors)
