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

            log.info("inferring injector and backend count to be 1 each")
            injectors = 1
            backends = 1

            if "injectors" in template or "backends" in template:
                log.info("template specifies injectors or backends")
                if "injectors" in template:
                    log.info("template specified injectors, reading count from template")
                    injectors = template["injectors"]
                    template["prop_options"][
                        injectors_specjbb_property_name] = injectors["count"]
                elif "backends" in template:
                    log.info("template specified backends, reading count from template")
                    backends = template["backends"]
                    template["prop_options"][
                        backends_specjbb_property_name] = backends["count"]
            elif "prop_options" in template:
                log.info("reading injector and backend count from 'prop_options'")
                # and let's peek for injector count (specjbb.txi.pergroup.count)
                injectors = template["prop_options"].get(
                    injectors_specjbb_property_name, 1)
                # and let's peek for backend count (specjbb.group.count)
                backends = template["prop_options"].get("specjbb.group.count",
                                                        1)
            else:
                log.info("could not find specified counts, using template defaults/ populated translations from arguments")
                template["prop_options"][
                    injectors_specjbb_property_name] = injectors
                template["prop_options"][
                    backends_specjbb_property_name] = backends

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
