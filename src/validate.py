import uuid
from schema import Schema, And, Or, Optional

# used for python2 and python3 string types
from six import text_type


def is_stringy(v):
    return type(v) is text_type

def random_run_id():
    """
    Returns a value that will be a default, non-repeated
    run ID used for a RunConfiguration object.
    """
    return uuid.uuid4().hex

TemplateDataSchema = Schema({
    "args": [is_stringy],
    Optional("run_type", default="composite"): And(is_stringy, lambda rt: rt.lower() in ["multi", "composite", "distributed_ctrl_txl", "distributed_sut"]),
    Optional("java", default="java"): is_stringy,
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
    Optional("tag"): is_stringy,
})

SpectateConfig = Schema({
    "TemplateData": {
        is_stringy: TemplateDataSchema,
    },
    "RunList": [RunConfigSchema],
})


def validate(unvalidated):
    d = SpectateConfig.validate(unvalidated)

    # each run needs a unique run id
    custom_run_ids = list(map(lambda run: run["tag"], 
        filter(lambda run: "tag" in run, d["RunList"])))

    if custom_run_ids and len(set(custom_run_ids)) != len(custom_run_ids):
        duplicates = [_id for _id in custom_run_ids if custom_run_ids.count(_id) > 1 ]
        raise Exception("Duplicate custom run IDs provided to different configured runs: {}".format(duplicates))

    # generate IDs for each unspecified run
    for run in list(filter(lambda run: "tag" not in run, d["RunList"])):
        run["tag"] = random_run_id()

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
