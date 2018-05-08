from schema import Schema, And, Or, Optional

# used for python2 and python3 string types
from six import text_type


def is_stringy(v):
    return type(v) is text_type

"""
These are valid SpecJBB components (what you'd pass into the '-m' flag to specjbb2015.jar).
"""
SpecJBBComponentTypes = [
    "backend",
    "txinjector",
    "composite",
    "multi",
    "distributed",
]

ComponentSchema = Schema({
    Optional("type"): And(is_stringy, lambda t: t.lower() in SpecJBBComponentTypes),
    Optional("count", default=1): int,
    Optional("options", default=[]): [is_stringy],
    Optional("jvm_opts", default=[]): [is_stringy],
    Optional("hosts", default=[]): [{
        "hostname": is_stringy,
        Optional("per"): int,
        }],
    })

TemplateSchema = Schema({
    "args": [is_stringy],
    Optional("run_type", default="composite"): And(is_stringy, lambda rt: rt.lower() in ["multi", "composite", "distributed"]),
    Optional("java", default="java"): is_stringy,
    Optional("jar", default="specjbb2015.jar"): is_stringy,
    Optional("port", default="50051"): is_stringy,
    Optional("injector_hosts"): Or(int, ComponentSchema, [{
            "host": is_stringy,
            "per": And(int, lambda x: x > 0),
            }],
    Optional("default_props"): {
        is_stringy: object,
    },
    Optional("annotations"): {
        is_stringy: is_stringy,
    },
    Optional("translations"): {
        is_stringy: is_stringy,
    },
    Optional("types"): {
        is_stringy: is_stringy,
    },
})

RunConfigSchema = Schema({
    "template_type": is_stringy,
    "args": {
        Optional(is_stringy): object,
    },
    Optional("props_extra"): {
        Optional(is_stringy): is_stringy,
    },
})

SpectateConfig = Schema({
    "TemplateData": {
        is_stringy: TemplateSchema,
    },
    "RunList": [RunConfigSchema],
})


def validate(unvalidated):
    d = SpectateConfig.validate(unvalidated)

    # each of the args that appear in the RunList,
    for run in d["RunList"]:
        # for the TemplateData they pull from,
        t = d["TemplateData"][run["template_type"]]

        # they need to appear in the template
        for arg in run["args"]:
            if arg not in t["args"]:
                raise Exception("Argument '{}' was not in the template {}'s arguments: {}".format(arg, run["template_type"], t["args"]))

        # and if the arg isn't in the run,
        # it needs to have a default
        for arg in t["args"]:
            if arg not in run["args"] and arg not in t["default_props"]:
                raise Exception("Argument '{}' did not have a default from template {}".format(arg, run["template_type"]))

    # for each template,
    for name, template in d["TemplateData"].items():
        # all of the translations need to refer to
        # arguments specified by the user
        if "translations" in template:
            for translation in template["translations"]:
                if translation not in template["args"]:
                    raise Exception("Translation '{}' for template '{}' doesn't have an associated argument".format(translation, name))
        # all of the annotations need to refer to
        # arguments specified by the user
        if "annotations" in template:
            for annotation in template["annotations"]:
                if annotation not in template["args"]:
                    raise Exception("Annotation '{}' for template '{}' doesn't have an associated argument".format(annotation, name))

    return d
