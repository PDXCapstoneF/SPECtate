from schema import Schema, And, Or, Optional, Use

# used for python2 and python3 string types
from six import text_type


def is_stringy(v):
    return type(v) is text_type

ValidRunTypes = ["multi", "composite", "distributed"]

DefaultJavaRunOptions = {
        "path": "java",
        "options": []
        }

JvmRunOptions = Schema(Or(
    And(None, Use(lambda _: DefaultJavaRunOptions)), 
    And(dict, {
        "path": is_stringy,
        "options": [is_stringy],
        }), 
    And(is_stringy, Use(lambda s: { "path": s, "options": [] })), 
    And([is_stringy], Use(lambda ss: { "path": ss[0], "options": ss[1:] }))))

TemplateSchema = Schema({
    "args": [is_stringy],
    Optional("run_type", default="composite"): And(is_stringy, lambda rt: rt.lower() in ValidRunTypes),
    Optional("java", default="java"): JvmRunOptions,
    Optional("jar", default="specjbb2015.jar"): is_stringy,
    Optional("prop_options"): {
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
    Optional("times", default=1): int,
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
            if arg not in run["args"] and arg not in t["prop_options"]:
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
