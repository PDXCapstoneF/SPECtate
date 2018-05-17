"""
This module defines a RunGenerator that:
    - is (partially) responsible for validating templates and runs given in a Tate config
    - is responsible for populating arguments, props etc
    - is responsible for generating the specific run's .props file
    - is responsible for giving the right arguments to a benchmark_run.SpecJBBRun so that it can do its thing

The intention is that you pass a Tate Config into the
RunGenerator, and it updates itself to have a list of
all the runs present in that configuration.
"""
import logging
from src.validate import TemplateDataSchema, RunConfigSchema, random_run_id


log = logging.getLogger(__name__)

injectors_specjbb_property_name = "specjbb.txi.pergroup.count"
backends_specjbb_property_name = "specjbb.group.count"
controller_distributed_property_name = "specjbb.controller.host"


def run_type_to_controller_type(rt):
    return {
        'distributed': 'distcontroller',
        'composite': 'composite',
        'multi': 'multicontroller',
    }.get(rt)


class RunGenerator:
    """
    This class is responsible for taking a Tate config and
    updating self.runs with a list of validated runs that
    you can then pass to benchmark_run.SpecJBBRun for a successful
    benchmarking run.

    The accompanying test module contains examples for how
    this should and shouldn't work.
    """

    def __init__(self, TemplateData=None, RunList=None):
        """
        Initializes this instance to hold all the validated runs in the
        provided configuration.

        :param TemplateData: A TemplateData object. (See src.validate.TemplateDataSchema)
        :param RunList: A list of RunConfig objects. (See src.validate.RunConfigSchema)
        """
        self.runs = []
        log.debug("recieved TemplateData: {}".format(TemplateData))
        log.debug("recieved RunList: {}".format(RunList))

        # let's go ahead and populate everything
        for run in RunList:
            run = RunConfigSchema.validate(run)
            template = TemplateData.get(run["template_type"])
            template = TemplateDataSchema.validate(template)
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

            if template["run_type"] == "distributed" and controller_distributed_property_name not in props:
                raise Exception("Controller IP not specified for a distributed run: define value or argument with translation for '{}'".format(controller_distributed_property_name))

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
                'tag':
                run["tag"] if "tag" in run else random_run_id(),
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
