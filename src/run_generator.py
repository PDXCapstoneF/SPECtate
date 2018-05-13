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
            injectors = props.get(injectors_specjbb_property_name, 1)
            # and let's peek for backend count (specjbb.group.count)
            backends = props.get(backends_specjbb_property_name, 1)

            if "injectors" in template:
                injectors = self._ensure_count_is_accurate(
                    key="injectors",
                    prop_name=injectors_specjbb_property_name,
                    template=template,
                    props=props)
            if "backends" in template:
                backends = self._ensure_count_is_accurate(
                    key="backends",
                    prop_name=backends_specjbb_property_name,
                    template=template,
                    props=props)

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

    def _ensure_count_is_accurate(self, key, prop_name, template, props):
        """
        Conditionally updates a component's count from props
        """
        log.info(
            "template specified {}, reading count from props we've already populated".
            format(key))
        component = template[key]

        if prop_name in props:
            # we've already set the count
            # and we need to override it
            # in injectors
            log.warn(
                "overriding template provided count with populated {} count".
                format(key))
            component["count"] = props.get[prop_name]
        else:
            # we've not yet set the count
            # and we need to set it in the
            # properties
            log.info("setting {} count from populated prop".format(key))
            props[prop_name] = component["count"]
        log.info("inferred component {}: {}".format(key, component))
        return component
