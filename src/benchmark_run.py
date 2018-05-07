"""
This module replaces `run.sh`.
"""

import os
import shutil
from multiprocessing import Pool
from uuid import uuid4
import logging
import configparser

from src.task_runner import TaskRunner

log = logging.getLogger(__name__)


class InvalidRunConfigurationException(Exception):
    """
    Exception thrown by SpecJBBRun when given a run configuration
    that it can't figure out. Optionally has an error message.
    """

    def __init__(self, msg="Run was invalid"):
        self.msg = msg

    def __str__(self):
        return self.msg


def do(task):
    """
    Runs a given task synchronously, with some debugging.
    The reason this is defined outside of the context of `SpecJBBRun.run()` is because
    this function needs to be pickle-able for `Pool.map` to be able to use it.
    """
    log.debug("starting task {}".format(task))
    task.run()
    log.debug("finished task {}".format(task))


class JvmRunOptions:
    """
    A helper class for SpecJBBRun, to provide defaults and a way
    for lists, dict etc to be coerced into something that SpecJBBRun can work with.
    """

    def __init__(self, val=None):
        """
        Initialize JvmRunOptions based on the type of val.
        If str: set path to val.
        If list: set path to val[0], and val[1:] as the options.
        If dict: validate that the dict has the required keys, and set the internal dict to val.
        """
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
        """
        Defined so that JvmRunOptions is subscriptable.
        """
        return self.__dict__.__getitem__(name)

    def __getattr__(self, name):
        """
        Defined so that JvmRunOptions can be accessed via attr names.
        """
        return self.__dict__.__getitem__(name)

    def __repr__(self):
        return "{}".format(self.__dict__)


"""
These are valid SpecJBB components (what you'd pass into the '-m' flag to specjbb2015.jar).
"""
SpecJBBComponentTypes = [
    "backend",
    "txinjector",
    "composite",
    "multi",
    "distributed",
]


class SpecJBBComponentOptions(dict):
    """
    A helper class for SpecJBBRun that provides a way to set defaults,
    and a way to coerce additional options into something that SpecJBBRun can work with.

    If rest is a dict, it will be validated, and the internal dict will be set to rest.
    If rest is an int, it will be interpreted as the count for this particular component.
    If rest is not provided, the internal dict will be set to the default.
    """

    def __init__(self, component_type, rest=None):
        if isinstance(component_type, str):
            component_type = component_type.lower()
            if component_type not in SpecJBBComponentTypes:
                raise Exception(
                    "invalid component type '{}' given to SpecJBBComponentOptions".format(component_type))
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
            raise Exception(
                "Unrecognized 'rest' given to SpecJBBComponentOptions: {}".format(rest))

    def __getitem__(self, name):
        """
        Defined so that SpecJBBComponentOptions is subscriptable.
        """
        return self.__dict__.__getitem__(name)

    def __getattr__(self, name):
        """
        Defined so that SpecJBBComponentOptions can be accessed via attr names.
        """
        return self.__dict__.__getitem__(name)

    def __repr__(self):
        return "{}".format(self.__dict__)


class SpecJBBRun:
    """
    Does a run!
    Handles .props file generation, jvm invocations (based on properties passed to __init__)
    and cleanup afterwards.
    """

    def __init__(self,
                 controller=None,
                 backends=None,
                 injectors=None,
                 java=None,
                 jar=None,
                 props={},
                 props_file='specjbb2015.props'):
        """
        Initialize a SpecJBBRun.

        Args:
            controller: The dictionary used to configure the controller. Must have a controller type, if it is a dictionary, and if not, the default controller type is "composite".
            backends: The dictionary, list, or int used to configure the number of backends for this particular run.
            injectors: The dictionary, list, or int used to configure the number of injectors for this particular run.
            java: Either the string used to invoke "java" on this machine, or a list of args to pass to Popen, or a dictionary with a "path" and "option" defined.
            jar: The relative or absolute path to the specjbb2015.jar file.
            props: The props that will be passed to the props file generated for this run. Keys look like ("com.spec.prop": "value").
            props_file: The relative or absolute path to the specjbb2015.props file that will be generated for this particular run.
        """
        if None in [java, jar] or not isinstance(jar, str):
            raise InvalidRunConfigurationException

        self.jar = os.path.abspath(jar)
        self.props = props
        self.props_file = props_file
        self.run_id = uuid4().hex
        self.log = logging.LoggerAdapter(log, {'run_id': self.run_id})

        self.java = JvmRunOptions(java)
        self.__set_topology__(controller, backends, injectors)

    def __set_topology__(self, controller, backends, injectors):
        """
        Sets the topology dictionaries (what controller type, 
        how many backends, how many injectors per backend, etc)
        based on what's passed into __init__.
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
            self.controller = SpecJBBComponentOptions(
                controller["type"], controller)

        self.backends = SpecJBBComponentOptions("backend", backends)
        self.injectors = SpecJBBComponentOptions("txinjector", injectors)

    def _generate_tasks(self):
        """
        Generator that yields TaskRunners for the backends and injectors
        with the correct JVM and SPECjbb2015 arguments for this particular run.
        """
        if self.controller["type"] == "composite":
            return

        self.log.info(
            "generating {} groups, each with {} transaction injectors"
                .format(self.backends["count"], self.injectors["count"]))

        for _ in range(self.backends["count"]):
            group_id = uuid4().hex
            backend_jvm_id = uuid4().hex
            self.log.debug("constructing group {}".format(group_id))
            yield TaskRunner(*self.backend_run_args(),
                             '-G={}'.format(group_id),
                             '-J={}'.format(backend_jvm_id))

            self.log.debug(
                "constructing injectors for group {}".format(group_id))

            for _ in range(self.injectors["count"]):
                ti_jvm_id = uuid4().hex
                self.log.debug(
                    "preparing injector in group {} with jvmid={}".format(group_id, ti_jvm_id))
                yield TaskRunner(*self.injector_run_args(),
                                 '-G={}'.format(group_id),
                                 '-J={}'.format(ti_jvm_id))

    def run(self):
        pwd = os.getcwd()
        results_directory = os.path.abspath(str(self.run_id))

        self.log.debug("set logging directory to {}".format(results_directory))

        try:
            self.log.debug(
                "attempting to create results directory {}".format(results_directory))
            try:
                os.mkdir(results_directory)
            except os.FileExistsError:
                self.log.debug(
                    "run results directory already existed, continuing")

            self._run()
        except Exception as e:
            self.log.error(
                "exception: {}, removing results directory".format(e))
            shutil.rmtree(results_directory)
        finally:
            os.chdir(pwd)
        return results_directory

    def _run(self):
        """
        Executes this particular SpecJBBRun by:
        - writing the props file for this run at self.props_file
        - setting up the controller and running its task
        - setting up the transaction injectors and backends and running their tasks
        - emmitting "done" messages when finished
        """
        # write props file (or ensure it exists)
        with open(self.props_file, 'w+') as props_file:
            c = configparser.ConfigParser()
            c.read_dict({'SPECtate': self.props})
            c.write(props_file)

        # setup jvms
        # we first need to setup the controller
        c = TaskRunner(*self.controller_run_args())
        self.dump()

        if self.controller["type"] == "composite":
            self.log.info("begin composite benchmark")
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
