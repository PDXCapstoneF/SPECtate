"""
This module replaces `run.sh`.
"""

from uuid import uuid4
import logging

from src.task_runner import TaskRunner

FORMAT = '%(asctime)-15s run_id=%(run_id)s: %(message)s'
logging.basicConfig(level=logging.INFO, format=FORMAT)
log = logging.getLogger(__name__)

class InvalidRunConfigurationException(Exception):
    pass

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
        self.props = props

        self.run_id = uuid4()
        self.log = logging.LoggerAdapter(log, { 'run_id': self.run_id })

    def _generate_tasks(self):
        self.log.info("generating {} groups, each with {} transaction injectors".format(self.props["backends"], self.props["injectors"]))

        for _ in range(self.props["backends"]):
            group_id = uuid4()
            backend_jvm_id = uuid4()
            self.log.debug("constructing group {}".format(group_id))
            yield TaskRunner(self.props["jvm"],
                '-jar', self.props["jar"],
                '-m', 'BACKEND',
                '-G={}'.format(group_id),
                '-J={}'.format(backend_jvm_id))

            self.log.debug("constructing injectors for group {}".format(group_id))

            for _ in range(self.props["injectors"]):
                ti_jvm_id = uuid4()
                self.log.debug("preparing injector in group {} with jvmid={}".format(group_id, ti_jvm_id))
                yield TaskRunner(self.props["jvm"],
                    '-jar', self.props["jar"],
                    '-m TXINJECTOR',
                    '-G={}'.format(group_id),
                    '-J={}'.format(ti_jvm_id))

    def run(self):
        # setup jvms
        # we first need to setup the controller
        controller_props = self.props['controller'] if 'controller' in self.props and isinstance(self.props['controller'], list) else self.props.get('controller', [])

        c = TaskRunner(self.props["jvm"],
                '-jar', self.props["jar"],
                '-m', 'MULTICONTROLLER',
                *controller_props)

        self.log.info("begin benchmark")

        # run benchmark
        c.run()
        
        tasks = [ task for task in self._generate_tasks() ]
        for task in tasks:
            self.log.debug("starting task {}".format(task))
            task.start()
            self.log.debug("started task {}".format(task))

        # TODO: collect results

    def dump(self, level=logging.DEBUG):
        """
        Dumps info about this currently configured run.
        """

        self.log.log(level, vars(self))
