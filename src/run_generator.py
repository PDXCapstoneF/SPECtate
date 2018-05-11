import logging
from src.validate import TemplateSchema, RunConfigSchema

log = logging.getLogger(__name__)

injectors_specjbb_property_name = "specjbb.txi.pergroup.count"
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
        log.debug("recieved TemplateData: {}".format(TemplateData))
        log.debug("recieved RunList: {}".format(RunList))

        # let's go ahead and populate everything
        for run in RunList:
            run = RunConfigSchema.validate(run)
            template = TemplateData.get(run["template_type"])
            template = TemplateSchema.validate(template)
            log.debug("run: {}".format(template))

            # populate prop_options
            props = template.get("prop_options", dict()).copy()
            # populate arguments
            if "translations" in template:
                props.update({
                    translation: run["args"][arg]
                    for arg, translation in template["translations"].items()
                })
            if "props_extra" in run:
                props.update(run["props_extra"])

            log.info("reading injector and backend count from 'prop_options'")
            # and let's peek for injector count (specjbb.txi.pergroup.count)
            injectors = props.get(
                injectors_specjbb_property_name, 1)
            # and let's peek for backend count (specjbb.group.count)
            backends = props.get(backends_specjbb_property_name, 1)

            if "injectors" in template or "backends" in template:
                log.info("template specifies injectors or backends")
                if "injectors" in template:
                    log.info("template specified injectors, reading count from props we've already populated")
                    injectors = template["injectors"]
                    injectors["count"] = props.get(injectors_specjbb_property_name, 1)
                elif "backends" in template:
                    log.info("template specified backends, reading count from props we've already populated")
                    backends = template["backends"]
                    backends["count"] = props.get(backends_specjbb_property_name, 1)

            controller = template.get("controller", dict())
            controller.update({
                "type":
                run_type_to_controller_type(template["run_type"]),
            })

            self.runs.append({
                'controller':
                controller,
                'backends':
                backends,
                'injectors':
                injectors,
                'java':
                template["java"],
                'jar':
                template["jar"],
                'times':
                run["times"],
                'props':
                props,
                'props_file':
                template.get("props_file", 'specjbb2015.props'),
            })
