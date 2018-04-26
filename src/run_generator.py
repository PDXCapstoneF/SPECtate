from src.validate import TemplateSchema, RunConfigSchema

class RunGenerator:
    def __init__(self, templates=None, runs=None):
        self.runs = []

        # let's go ahead and populate everything
        for run in runs:
            run = RunConfigSchema.validate(run)
            template = templates.get(run["template_name"])
            template = TemplateSchema.validate(template)

            if "default_props" in template:
                # and let's peek for injector count (specjbb.txi.pergroup.count)
                injectors = props.get("specjbb.txi.pergroups.count", 1)
                # and let's peek for backend count (specjbb.group.count)
                backends = props.get("specjbb.group.count", 1)
            else:
                injectors = 1
                backends = 1

            self.runs.append({
                'controller': {
                    "type": template["run_type"],
                },
                'backends': backends, 
                'injectors': injectors,
                'java': template["java"],
                'jar': template["jar"],
                'invocations': template["invocations"],
            })
