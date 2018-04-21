import subprocess

class TaskRunner:
    """
    Runs a specified task with the given options.
    """
    def __init__(self, path, *options, **kw):
        if not path:
            raise Exception

        self.path = path

        for opt in options:
            if not isinstance(opt, str):
                raise Exception

        self.options = list(options)
        self.kw = kw


    def argument_list(self):
        return [self.path] + self.options

    def run(self):
        return subprocess.run(self.argument_list(), stdin=True, check=True, **self.kw)
