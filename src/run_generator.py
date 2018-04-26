class RunGenerator:
    def __init__(self, templates=None, runs=None):
        # let's go ahead and populate everything
        for run in runs:
            props = templates.get(run["template_type"])

            # and let's peek for injector count (specjbb.txi.pergroup.count)
            injectors = props["specjbb.txi.pergroups.count"]
            # and let's peek for backend count (specjbb.group.count)
            injectors = props["specjbb.group.count"]

            self.runs.append(**{
                'controller': None, # TODO: this needs to come from somewhere
                'backends': backends, 
                'injectors': injectors,
                'java': None, # TODO: this needs to come from somewhere
                'jar': None, # TODO: this needs to come from somewhere
                'invocations': "{java} {spec}" # TODO: where should this come from?
            }):

        pass
