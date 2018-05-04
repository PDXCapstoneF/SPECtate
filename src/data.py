from os import path
import yaml
from boltons.cacheutils import cachedproperty
import operator

from src import objects


def get_operator_fn(op):
    """
    Returns a builtin operator based on the comparator
    that the argument represents.

    :param op: A single character that's a comparator (<, >, <=, >=).
    :return: A builtin operator
    """
    return {
        '<': operator.lt,
        '<=': operator.le,
        '>': operator.gt,
        '>=': operator.ge,
        '=': operator.eq,
    }[op]


def constraint_string(s):
    """
    Returns a lambda that constrains a value x based on
    a value interpolated from the argument.

    :param s: A string that looks like "< 0"
    :returns: A predicate based on s.
    """
    op, *num = s.split()

    def satisfies(x):
        if not num:
            return False

        try:
            n = int(num[0])
        except Exception:
            n = float(num[0])

        try:
            return get_operator_fn(op)(x, n)
        except:
            return False

    return satisfies


def to_propitem(data_item):
    """
    Returns a objects.propitem based on the argument.

    :param data_item: A key, value pair where key is the name of the string property and value is a dictionary with more information about that property
    :returns: One objects.propitem
    """
    specjbb_property_name, values = data_item

    def missing(key, e):
        raise Exception("Missing {} for configuration value {}: {}".format(
            key, specjbb_property_name, e))

    try:
        default_value = values["default"]
    except Exception as e:
        missing("default")

    try:
        annotation = values["annotation"]
    except Exception as e:
        missing("annotation")

    # infer the input validator from the
    # type of the default_value
    if isinstance(default_value, int):
        input_validator = objects.number_validator
    elif isinstance(default_value, float):
        input_validator = objects.float_validator
    else:
        input_validator = objects.default_validator

    valid_options = None
    help_text = ""

    # get the value validator function
    if "allowed" not in values or values["allowed"] == "any":
        # allow anything
        value_validator = lambda _: True
    else:
        # is allowed a dict?
        allowed = values["allowed"]

        if isinstance(allowed, str):
            # allowed is a constraint string
            value_validator = constraint_string(allowed)
        elif isinstance(allowed, dict):
            # allowed is more complex
            if "type" not in allowed and "within" not in allowed:
                raise Exception(
                    "Not given a valid 'allowed' specification for {}".format(
                        specjbb_property_name))

            if "type" in allowed:
                # type is either a constraint string,
                # or a list like an enum
                t = allowed["type"]
                help_text = allowed.get("text", None)

                if isinstance(t, str):
                    value_validator = constraint_string(t)
                elif isinstance(t, list):
                    # get valid_opts
                    value_validator = lambda x: x in t
                    valid_options = t
                else:
                    raise Exception(
                        "Invalid 'type' specification for 'allowed' in {}: {}".
                        format(specjbb_property_name, t))

            elif "within" in allowed:
                # within is a list of constraint strings
                w = allowed["within"]
                if not isinstance(w, list):
                    raise Exception("'within' not a list for {}: {}".format(
                        specjbb_property_name, w))
                value_validator = lambda x: all(map(lambda f: f(x), map(constraint_string, w)))
        else:
            raise Exception("Unknown 'allowed' type given for {}: {}".format(
                specjbb_property_name, allowed))

    if not value_validator(default_value):
        # "WARNING: default value for property {} didn't pass validation: {}".format(specjbb_property_name, default_value)
        pass

    return objects.propitem(
        specjbb_property_name,
        default_value,
        annotation,
        input_validator,
        value_validator,
        valid_opts=valid_options,
        help_text=help_text,
    )


class DataLoader:
    """
    Responsible for loading data from 'data.yml', which is a big
    list of annotations, constraints, help text and defaults for
    all of the options provided in specjbb2015.props.
    """

    def __init__(self, data_file="data.yml"):
        """
        Initializes this DataLoader.

        :param data_file: String that is a relative filename
        """
        self.data_file = data_file
        _current_file_path = path.abspath(path.dirname(__file__))
        self.data_file_path = path.join(_current_file_path, self.data_file)

    @cachedproperty
    def data(self):
        """
        Returns the raw data from the configured data file.
        Will return the same value each time it's called after
        the first time, even if the data file changes.

        (See <http://boltons.readthedocs.io/en/latest/cacheutils.html#boltons.cacheutils.cachedproperty>)
        """
        with open(self.data_file_path) as dfp:
            self.data = yaml.load(dfp)
        return self.data

    @cachedproperty
    def as_propitem(self):
        """
        Returns the raw data from the configured data file as
        objects.propitems.
        Will return the same value each time it's called after
        the first time, even if the data file changes.

        (See <http://boltons.readthedocs.io/en/latest/cacheutils.html#boltons.cacheutils.cachedproperty>)
        """
        self.propitem = list(map(to_propitem, self.data.items()))
        return self.propitem

    @staticmethod
    def defaults():
        """
        Returns the exact same thing as objects.defaults, but
        using 'data.yml' rather than the definition in objects.
        """
        return DataLoader().as_propitem
