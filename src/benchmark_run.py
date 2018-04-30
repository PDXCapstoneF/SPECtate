"""
This module replaces `run.sh`.
"""

from multiprocessing import Pool
from uuid import uuid4
import logging
import configparser

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


class JvmRunOptions:
    def __init__(self, val=None):
        if isinstance(val, str):
            self.__dict__ = {
                "path": val,
                "options": [],
            }
        elif isinstance(val, list):
            self.__dict__ = {
                "path": val[0],
                "options": val[1:],
            }
        elif isinstance(val, dict):
            if "path" not in val:
                raise Exception("'path' not specified for JvmRunOptions")
            if not isinstance(val["path"], str):
                raise Exception("'path' must be a string")
            if "options" not in val:
                val["options"] = []
            elif not isinstance(val["options"], list):
                raise Exception("'path' must be a string")

            self.__dict__ = val
        elif val is None:
            self.__dict__ = {
                "path": "java",
                "options": []
            }
        else:
            raise Exception(
                "unrecognized type given to JvmRunOptions: {}".format(type(val)))

    def __getitem__(self, name):
        return self.__dict__.__getitem__(name)

    def __getattr__(self, name):
        return self.__dict__.__getitem__(name)


SpecJBBComponentTypes = [
    "backend",
    "txinjector",
    "composite",
    "multi",
    "distributed",
]


class SpecJBBComponentOptions(dict):
    def __init__(self, component_type, rest=None):
        if isinstance(component_type, str):
            if component_type not in SpecJBBComponentTypes:
                raise Exception("invalid component type '{}' given to SpecJBBComponentOptions".format(component_type))
        else:
            raise Exception(
                "Unrecognized type given to SpecJBBComponentOptions: {}".format(type(component_type)))

        if isinstance(rest, dict):
            if "count" not in rest:
                rest["count"] = 1
            if "options" not in rest:
                rest["options"] = []
            if "jvm_opts" not in rest:
                rest["jvm_opts"] = []

            rest["type"] = component_type

            self.__dict__ = rest
        elif isinstance(rest, int):
            self.__dict__ = {
                "type": component_type,
                "count": rest,
                "options": [],
                "jvm_opts": []
            }
        elif rest is None:
            self.__dict__ = {
                "type": component_type,
                "count": 1,
                "options": [],
                "jvm_opts": []
            }
        else:
            raise Exception("Unrecognized 'rest' given to SpecJBBComponentOptions: {}".format(rest))

    def __getitem__(self, name):
        return self.__dict__.__getitem__(name)

    def __getattr__(self, name):
        return self.__dict__.__getitem__(name)

class SpecJBBRun:
    """
    Does a run!
    """

    def __init__(self,
                 controller=None,
                 backends=None,
                 injectors=None,
                 java=None,
                 jar=None,
                 props={},
                 props_file='specjbb2015.props'):
        if None in [java, jar] or not isinstance(jar, str):
            raise InvalidRunConfigurationException

        self.jar = jar
        self.props = props
        self.props_file = props_file
        self.run_id = uuid4()
        self.log = logging.LoggerAdapter(log, {'run_id': self.run_id})

        self.java = JvmRunOptions(java)
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
            self.controller = SpecJBBComponentOptions("composite")
        else:
            self.controller = SpecJBBComponentOptions(controller["type"], controller)

        self.backends = SpecJBBComponentOptions("backend", backends)
        self.injectors = SpecJBBComponentOptions("txinjector", injectors)

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
        # write props file (or ensure it exists)
        with open(self.props_file, 'w+') as props_file:
            c = configparser.ConfigParser()
            c.read_dict({'SPECtate': self.props})
            c.write(props_file)
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
        self.log.debug(
            "full options being generated from: {}".format(options_dict))

        java = [self.java["path"], "-jar", self.jar] + \
            self.java["options"] + options_dict.get("jvm_opts", [])
        spec = ["-m", options_dict["type"].upper()] + \
            options_dict.get("options", []) + ["-p", self.props_file]

        self.log.debug("java: {}, spec: {}".format(java, spec))

        return java + spec

    def controller_run_args(self):
        return self._full_options(self.controller)

    def backend_run_args(self):
        return self._full_options(self.backends)

    def injector_run_args(self):
        return self._full_options(self.injectors)
