from schema import Schema, And, Optional

ConfigSchema = Schema({
    "run_type": And(str, 
        lambda rt: rt in ["single", "multi", "distributed"]),
        Optional("meta"): {
        object: object
    },

    "speccjbb": {
        "injectors": And(int, lambda n: n > 0),
        "backends": And(int, lambda n: n > 0),
        "jvm_path": str,
        "jar_path": str,
    },

    "jvm_options": [str],

    "props": {
        str: str,
    },

    "other": {
        str: str,
    }
    })

def validate(unvalidated):
    return ConfigSchema.validate(unvalidated)
