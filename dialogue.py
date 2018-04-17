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


# Utility functions.
def print_dict(d):
    for key, value in sorted(d.items(), key=lambda x : x[0]):
        print("{}: {}".format(key, value))


# Level-one layer of dialogue.
def print_all_runs(run_dict, runtype_dict):
    for k, v in sorted(run_dict.items(), key=lambda x : x[0]):
        print('Run {}'.format(k))
        print_dict(v)


def create_run(run_dict, runtype_dict):
    run_name = input('Input a name for the run. ')
    if run_name in run_dict:
        print('{} is already in the dict!'.format(run_name))
        return

    print('Input the run type. Current options: {}'.format(
            ' '.join(sorted(runtype_dict.keys()))))
    run_type = input('-> ')
    if run_type not in runtype_dict.keys():
        user_input = input('{} is not currently an option. Add it? ')
        if user_input.lower() in ['y', 'yes']:
            create_runtype(runtype_dict)
        return
    run_dict[run_name] = create_run_dialogue(runtype_dict[run_type])


def create_runtype(run_dict, runtype_dict):
    option_set = set()
    user_input = input('Input a name for the runtype. ')
    while (user_input in runtype_dict and
           user_input.lower() not in ['q', 'quit']):
        user_input = ('Name already exists. Input a different name. ')

    runtype_name = user_input

    while user_input.lower() not in ['q', 'quit']:
        user_input = input('Input a new run attribute. ')
        if user_input in option_set:
            print('{} has already been added!'.format(user_input))
        option_set.add(user_input)
    
    if runtype_name.lower() not in ['q', 'quit']:
        runtype_dict[runtype_name] = list(option_set)


def delete_run(run_dict, runtype_dict):
    try:
        print('Input the tag of the run you want to delete.')
        print('Current run tags are: {}.'.format(
            ' '.join(sorted(run_dict.keys()))))
        user_input = input('-> ')
        del run_dict[user_input]
    except:
        print('Unable to remove tag {}.'.format(user_input))
        return
    print('Run deleted.')


def copy_run(run_dict, runtype_dict):
    try:
        print('Input the tag of the run you want to copy.')
        print('Current run tags are: {}.'.format(
            ' '.join(sorted(run_dict.keys()))))
        old_run = input('-> ')
        new_run = input('Input the new run tag. ')
        # Deep copy is required.
        run_dict[new_run] = {k : v for k, v in run_dict[old_run].items()}
    except:
        print('Unable to copy tag {}.'.format(old_run))
    print('Run copied to {}.'.format(new_run))


def edit_run(run_dict, runtype_dict):
    try:
        print('Input the tag of the run you want to edit.')
        print('Current run tags are: {}.'.format(
            ' '.join(sorted(run_dict.keys()))))
        run_tag = input('-> ')
        edit_run_dialogue(run_dict[run_tag])
    except:
        print('Unable to edit tag {}.'.format(index))
        return
    print('Run edited.')


def save_runlist(run_dict, runtype_dict):
    filename = input('Input a filename to save the RunDict. ')
    try:
        write_json(filename, run_dict)
    except:
        print('Unable to save to {}'.format(filename))
        return
    print('Saved to {}'.format(filename))


def load_runlist(run_dict, runtype_dict):
    filename = input('Input a filename to load a RunDict from. ')
    try:
        run_dict = read_json(filename)
    except:
        print('Unable to load from {}'.format(filename))
        return
    print('RunDict loaded from {}'.format(filename))


def new_runlist(run_dict, runtype_dict):
    user_input = input('Are you sure? This will remove all runs from the RunDict!')
    if user_input.lower() in ['y', 'yes']:
        run_dict = {}
        print('RunDict has been cleared.')
    else:
        print('RunDict has not been modified.')


def error(run_dict, runtype_dict):
    print('Invalid input.')


def create_run_dialogue(arg_list):
    new_run = {}
    for arg in arg_list:
        new_run[arg] = input("Input value for {}: ".format(arg))
    return new_run


def edit_run_dialogue(old_run):
    new_run = {}
    for key, value in sorted(old_run.items(), key=lambda x : x[0]):
        new_run[key] = input("Input value for {}. Current value = {}. ".format(
                             key, value))
    return new_run


def dialogue():
    """
    A dialogue function for creating a RunDict.
    Note that this currently does not allow you to create a new category of Run.
    """

    default_json = 'example_config.json'
    default_runtype = 'runtype_options.json'

    json_filename = input('Input RunDict filename. Default = ' +
                          '{}: '.format(default_json))
    runtype_filename = input('Input RunDict filename. Default = ' +
                          '{}: '.format(default_runtype))

    if not json_filename:
        json_filename = default_json

    if not runtype_filename:
        runtype_filename = default_runtype

    function_dict = {
        'print' : print_all_runs,
        'create' : create_run,
        'create runtype' : create_runtype,
        'delete' : delete_run,
        'copy' : copy_run,
        'edit' : edit_run,
        'save' : save_runlist,
        'load' : load_runlist,
        'new' : new_runlist
    }

    option_description_dict = {
        'print' : 'Print all runs',
        'create' : 'Create a new run',
        'delete' : 'Delete a run',
        'copy' : 'Copy a run',
        'edit' : 'Edit a run',
        'save' : 'Save a run',
        'load' : 'Load another run',
        'new' : 'New run'
    }

    try:
        run_dict = read_json(json_filename)
        runtype_dict = read_json(runtype_filename)
    except:
        print("Unable to open files.")
        return
    print("Loading succeeded.")

    user_input = ""

    while user_input.lower() not in ['q', 'quit']:
        print("What would you like to do?")
        print_dict(option_description_dict)
        user_input = input("-> ")
        if user_input.lower() not in ['q', 'quit']:
            function_dict.get(user_input, error)(run_dict, runtype_dict)
    print('Exiting.')
