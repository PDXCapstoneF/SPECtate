import json

def write_json(filename, python_dict):
    '''Serializes a python_dict and writes it to filename.'''
    with open(filename, 'w') as f:
        json.dump(python_dict, f, indent=4)

def read_json(filename):
    '''Reads a json file and loads it into a dictionary.'''
    with open(filename) as f:
        return json.load(f)

def create_run_dict(runtype, *args):
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
    return create_run_dict(runtype, *args)

def create_run_sh_invocation(run_dict):
    try:
        runtype_option_dict = read_json('runtype_options.json')
        parameters = runtype_option_dict[run_dict['Run Type']]
        return './run.sh {}'.format(
            ' '.join(str(run_dict[p]) for p in parameters))
    except: # Probably a dictionary failure.
        return ''


def execute_run(run_dict):
    # We'll eventually invoke this for realsies. For now, we're just going to
    # print it.
    invocation = create_run_sh_invocation(run_dict)
    if invocation:
        print(invocation)
        return True
    return False

def execute_runs(run_dict_list):
    return [execute_run(run_dict) for run_dict in run_dict_list]

           


        
