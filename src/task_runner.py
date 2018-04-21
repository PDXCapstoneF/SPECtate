import subprocess

class TaskRunner:
    """
    Runs a specified task with the given options.
    """
    def __init__(self, path, *options, **popen_kw):
        if not path:
            raise Exception

        self.path = path

        for opt in options:
            if not isinstance(opt, str):
                raise Exception

        self.options = list(options)
        self.kw = popen_kw

        self.proc = None


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
            return

        self.proc.terminate()

    def start(self):
        """
        Starts a configured task, if not already running.
        """
        if self.proc:
            return

        self.proc = subprocess.Popen(self.argument_list(), **self.kw)
