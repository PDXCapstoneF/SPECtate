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

    def run(self):
        pass

    def dump(self, level=logging.DEBUG):
        """
        Dumps info about this currently configured run.
        """
        def l(*a, **kw):
            log.log(level, *a, extra={'run_id': self.run_id}, *kw)

        l(vars(self))

        pass
