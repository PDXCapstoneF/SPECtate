"""
This module replaces `run.sh`.
"""

import logging
logging.basicConfig(level=logging.DEBUG)
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

    def run(self):
        pass

    def debug(self, logger=log, level=logging.DEBUG):
        """
        Dumps info about this currently configured run.
        """
        pass
