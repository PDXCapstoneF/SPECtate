import subprocess
import itertools
import logging

log = logging.getLogger(__name__)


class TaskRunner:
    """
    Runs a specified task with the given options.
    """

    def __init__(self, path, *options, **popen_kw):
        if not path:
            raise Exception("Path not specified for executable")

        self.path = path
        options = list(options)

        for opt in options:
            if not isinstance(opt, str):
                raise Exception("Option key was '{}':{}, not str".format(
                    opt, type(opt)))

        self.options = options
        self.kw = popen_kw

        self.proc = None

    def __str__(self):
        return "TaskRunner(path={}, options={}, kw={})".format(
            self.path, self.options, self.kw)

    def argument_list(self):
        return [self.path] + self.options

    def run(self, timeout=-1):
        """
        Runs a task synchronously and returns data from standard out.
        """
        self.start()

        out, err = self.proc.communicate(timeout)

        return out

    def stop(self):
        """
        Stops this running task, if applicable.
        """
        if not self.proc:
            log.debug("process already stopped")
            return

        return self.proc.terminate()

    def start(self):
        """
        Starts a configured task, if not already running.
        """
        if self.proc:
            log.warn("process already started")
            return

        log.debug("starting task with following argument set: {}".format(" ".join(self.argument_list())))

        self.proc = subprocess.Popen(self.argument_list(), **self.kw)
