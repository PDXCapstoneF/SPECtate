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

    def __init__(self, types={}, props={}):
        pass

    def run(self):
        pass

    def dump_info(self, level=logging.INFO):
        """
        Dumps info about this currently configured run.
        """
        pass
