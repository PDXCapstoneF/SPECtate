#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Serializes/deserializes json objects containing run-type configurations.
# Invokes run.sh with configurations stored in the file
# 'runtype_options.json'


import json

def write_json(filename, python_dict):
    """
    Serialize python_dict (dictionary) to filename (text file).
    :param filename: string
    :param python_dict: dict
    """
    with open(filename, 'w') as f:
        json.dump(python_dict, f, indent=4)

def read_json(filename):
    """
    Deserializes json formatted string from filename (text file) as a dictionary.
    :param filename: string
    """
    with open(filename) as f:
        return json.load(f)

def create_run_dict(runtype, *args):
    """
    Returns a dictionary of a run-type option object deserialized
    from a human-readable configuration file (e.g., JSON, HJSON, YAML).
    :param runtype: (HBIR || HBIR_RT || PRESET || LOADLEVEL)
    """
    runtype_option_dict = read_json('runtype_options.json')
    if runtype not in runtype_option_dict:
        return {}
    parameter_list = runtype_option_dict[runtype]

    if(len(parameter_list) == len(args)):
        return_dict = {tup[0] : tup[1] for tup in zip(parameter_list, args)}
        return_dict['Run Type'] = runtype
        return return_dict
    return {}

def create_run_dict_list(runtype, args):
    """
    Returns a dictionary of run-type option objects.
    :param runtype: (HBIR || HBIR_RT || PRESET || LOADLEVEL)
    """
    return create_run_dict(runtype, *args)

def create_run_sh_invocation(run_dict):
    """
    Builds a string to be used to invoke the `run.sh` script in ~/workloads. The
    command-line arguments of `run.sh` are initialized with the respective values in
    run_dict.
    :param run_dict: dict
    """
    try:
        runtype_option_dict = read_json('runtype_options.json')
        parameters = runtype_option_dict[run_dict['Run Type']]
        return './run.sh {}'.format(
            ' '.join(str(run_dict[p]) for p in parameters))
    except: # Probably a dictionary failure.
        return ''


def execute_run(run_dict):
    """
    Invoke the `run.sh` script in ~/workloads with command-line arguments stored
    in run_dict.
    :param run_dict: dict
    """
    # We'll eventually invoke this for realsies. For now, we're just going to
    # print it.
    invocation = create_run_sh_invocation(run_dict)
    if invocation:
        print(invocation)
        return True
    return False

def execute_runs(run_dict_list):
    """
    A wrapper for `execute_run(...)`, which is invoked repeatedly for each set
    of run-type options found in run_dict_list.
    :param run_dict_list: [dict]
    """
    return [execute_run(run_dict) for run_dict in run_dict_list]
