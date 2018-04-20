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

    def __init__(self, types=None, props=None):
        if not types or not props:
            raise InvalidRunConfigurationException
        self.types = types
        self.props = props
        self.run_id = uuid4()

    def run(self):
        pass

    def dump(self, level=logging.DEBUG):
        """
        Dumps info about this currently configured run.
        """
        def l(*a, **kw):
            log.log(level, *a, extra={'run_id': self.run_id}, *kw)

        l('types: {}'.format(self.types))
        l('props: {}'.format(self.props))

        pass
