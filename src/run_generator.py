import logging
from src.validate import TemplateSchema, RunConfigSchema

log = logging.getLogger(__name__)

injectors_specjbb_property_name = "specjbb.txi.pergroups.count"
backends_specjbb_property_name = "specjbb.group.count"

def run_type_to_controller_type(rt):
    return {
        'distributed': 'distcontroller',
        'composite': 'composite',
        'multi': 'multicontroller',
    }.get(rt)


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
                    template["default_props"][injectors_specjbb_property_name] = injectors["count"]
                elif "backends" in template:
                    backends = template["backends"]
                    template["default_props"][backends_specjbb_property_name] = backends["count"]
            elif "default_props" in template:
                # and let's peek for injector count (specjbb.txi.pergroup.count)
                injectors = template["default_props"].get(
                    injectors_specjbb_property_name, 1)
                # and let's peek for backend count (specjbb.group.count)
                backends = template["default_props"].get(
                    "specjbb.group.count", 1)
            else:
                template["default_props"][injectors_specjbb_property_name] = injectors
                template["default_props"][backends_specjbb_property_name] = backends

            controller = template.get("controller", dict())
            controller.update({
                    "type": run_type_to_controller_type(template["run_type"]),
                    })


            self.runs.append({
                'controller': controller,
                'backends': backends,
                'injectors': injectors,
                'java': template["java"],
                'jar': template["jar"],
                'props': props,
                'props_file': template.get("props_file", 'specjbb2015.props'),
            })
