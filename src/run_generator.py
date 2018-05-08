import logging
from src.validate import TemplateSchema, RunConfigSchema

log = logging.getLogger(__name__)

class RunGenerator:
    def __init__(self, TemplateData=None, RunList=None):
        self.runs = []
        log.debug("recieved TemplateData: {}, RunList: {}".format(TemplateData, RunList))

        # let's go ahead and populate everything
        for run in RunList:
            run = RunConfigSchema.validate(run)
            template = TemplateData.get(run["template_type"])
            template = TemplateSchema.validate(template)
            log.debug("run: {}".format(template))

            # populate default_props
            props = template.get("default_props", dict()).copy()
            # populate arguments
            if "translations" in template:
                props.update(
                    {translation: run["args"][arg] for arg, translation in template["translations"].items()})
            if "props_extra" in run:
                props.update(run["props_extra"])

            injectors = 1
            backends = 1

            if "injectors" in template or "backends" in template:
                if "injectors" in template:
                    injectors = template["injectors"]
                elif "backends" in template:
                    backends = template["backends"]
            elif "default_props" in template:
                # and let's peek for injector count (specjbb.txi.pergroup.count)
                injectors = template["default_props"].get(
                    "specjbb.txi.pergroups.count", 1)
                # and let's peek for backend count (specjbb.group.count)
                backends = template["default_props"].get(
                    "specjbb.group.count", 1)

            self.runs.append({
                'controller': {
                    "type": template["run_type"],
                },
                'backends': backends,
                'injectors': injectors,
                'java': template["java"],
                'jar': template["jar"],
                'props': props,
                'props_file': template.get("props_file", 'specjbb2015.props'),
            })
