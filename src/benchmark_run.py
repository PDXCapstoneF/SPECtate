"""
This module replaces `run.sh`.
"""

from uuid import uuid4
import logging

FORMAT = '%(asctime)-15s run_id=%(run_id)s: %(message)s'
logging.basicConfig(level=logging.DEBUG, format=FORMAT)
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
        if not types or not props or not args:
            raise InvalidRunConfigurationException

        self.args = args
        self.types = types
        self.translations = translations
        self.props = props

        self.run_id = uuid4()
        self.log = logging.LoggerAdapter(log, { 'run_id': self.run_id })

    def _generate_tasks(self):
        for group_id in range(self.props["backends"]):
            yield TaskRunner(self.props["jvm"],
                '-jar {}'.format(self.props["specjbb"]["jar"]),
                '-m BACKEND',
                '-G={}'.format(group_id),
                '-J={}'.format(uuid4()))
            for ti_num in range(self.props["injectors"]):
                yield TaskRunner(self.props["jvm"],
                    '-jar {}'.format(self.props["specjbb"]["jar"]),
                    '-m TXINJECTOR',
                    '-G={}'.format(group_id),
                    '-J={}'.format(uuid4()))

    def run(self):
        # setup jvms
        # we first need to setup the controller
        controller_props = props['controller'] if isinstance(props['controller'], list) else props['controller']

        c = TaskRunner(self.props["jvm"],
                *controller_props,
                '-jar {}'.format(self.props["specjbb"]["jar"]),
                '-m MULTICONTROLLER')

        self.log.info("begin benchmark")

        # run benchmark
        c.run()

        for task in self._generate_tasks():
            task.run()

        # TODO: collect results

    def dump(self, level=logging.DEBUG):
        """
        Dumps info about this currently configured run.
        """

        self.log.log(level, vars(self))
