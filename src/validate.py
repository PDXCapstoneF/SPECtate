from schema import Schema, And, Or, Optional

# used for python2 and python3 string types
from six import string_types

def is_stringy(v):
    return type(v) in [*string_types]

ConfigSchema = Schema({
    "run_type": And(is_stringy,
        lambda rt: rt in ["single", "multi", "distributed"]),
        Optional("meta"): {
        object: object
    },

    "speccjbb": {
        "injectors": And(int, lambda n: n > 0),
        "backends": And(int, lambda n: n > 0),
        "jvm_path": is_stringy,
        "jar_path": is_stringy,
    },

    "jvm_options": [is_stringy],

    "props": {
        object: object,
    },

    "other": {
        object: object,
    }
    })

def validate(unvalidated):
    return ConfigSchema.validate(unvalidated)
