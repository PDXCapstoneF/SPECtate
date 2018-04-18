from schema import Schema, And, Or, Optional

# used for python2 and python3 string types
from six import text_type

def is_stringy(v):
    return type(v) is text_type

ConfigSchema = Schema({
    Optional("meta"): {
        object: object
    },

    "specjbb": {
        "run_type": And(is_stringy,
            lambda rt: rt.lower() in ["hbir", "hbir_rt", "preset", "loadlevel"]),
        "kit_version": is_stringy,
        "tag": is_stringy,
        "jdk": is_stringy,
        "numa_node": int,
        "data": is_stringy,
        "rt_start": int,
        "duration": int,
        "t": [int],
    "jvm_options": [is_stringy],
    },

    })

def validate(unvalidated):
    return ConfigSchema.validate(unvalidated)
