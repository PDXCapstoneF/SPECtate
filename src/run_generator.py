import os
from src.validate import TemplateSchema, RunConfigSchema


class RunGenerator:
    def __init__(self, TemplateData=None, RunList=None):
        self.runs = []

        # let's go ahead and populate everything
        for run in RunList:
            run = RunConfigSchema.validate(run)
            template = TemplateData.get(run["template_type"])
            template = TemplateSchema.validate(template)

            # populate prop_options
            props = template.get("prop_options", dict()).copy()
            # populate arguments
            if "translations" in template:
                props.update(
                    {translation: run["args"][arg] for arg, translation in template["translations"].items()})
            if "props_extra" in run:
                props.update(run["props_extra"])

            if "prop_options" in template:
                # and let's peek for injector count (specjbb.txi.pergroup.count)
                injectors = template["prop_options"].get(
                    "specjbb.txi.pergroups.count", 1)
                # and let's peek for backend count (specjbb.group.count)
                backends = template["prop_options"].get(
                    "specjbb.group.count", 1)
            else:
                injectors = 1
                backends = 1

            self.runs.append({
                'controller': {
                    "type": template["run_type"],
                },
                'backends': backends,
                'injectors': injectors,
                'cwd': template["cwd"] if "cwd" in template else os.getcwd(),
                'java': template["java"],
                'jar': template["jar"],
                'times': run["times"],
                'props': props,
                'props_file': template.get("props_file", 'specjbb2015.props'),
            })
