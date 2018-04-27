import json

EXIT_CONSTS = set(['q', 'quit', 'exit'])
YES_CONSTS = set(['y', 'yes'])
HELP_CONSTS = set(['?', 'help'])

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

def print_dict(d):
    for key, value in sorted(d.items(), key=lambda x : x[0]):
        print("{}: {}".format(key, value))

# Level-one layer of dialogue. All functions take run_dict, runtype_dict as
# arguments so that they can be called homogeneously from a dictionary in
# `dialogue`. All functions must, in turn, *return* a tuple (run_dict,
# runtype_dict) as arguments.

def print_all_runs(run_list, runtype_dict):
    """
    Prints all runs in the RunList. Note that it gets the argument order from
    `runtype_dict`.
    """
    for run in run_list:
        print('\nTemplate Type: {}'.format(run['template_type']))
        for arg in runtype_dict[run['template_type']]['args']:
            print('{}: {}'.format(arg, run['args'][arg]))
        print()
    return (run_list, runtype_dict)

def error(run_dict, runtype_dict):

    print('Invalid input.')
    return run_dict, runtype_dict


def dialogue():
    """
    A dialogue function for creating, editing, and saving TateConfig objects
    as JSON objects.
    """

    default_json = 'example_config2.json'

    json_filename = input('Input TateConfig filename. Default = {} '\
                          .format(default_json))
    if not json_filename:
        json_filename = default_json

    function_dict = {
        'print' : print_all_runs,
    }

    option_description_dict = {
        'print' : 'Print all runs',
    }

    try:
        tate_config = read_json(json_filename)
        run_list = tate_config['RunList']
        template_dict = tate_config['TemplateData']
    except:
        user_input = input("Unable to open file. Open a blank file? ")
        if user_input not in YES_CONSTS:
            return
        run_list = []
        template_dict = {}
    if run_list and template_dict:
        print('TateConfig successfully loaded.')
    else:
        print('Blank TateConfig created.')

    user_input = ""

    while user_input.lower() not in EXIT_CONSTS:
        print("\nWhat would you like to do?\n")
        print_dict(option_description_dict)
        user_input = input("-> ")
        if user_input.lower() in HELP_CONSTS:
            continue
        elif user_input.lower() not in EXIT_CONSTS:
            run_list, template_dict = function_dict.get(user_input, error)(run_list, template_dict)
    print('Exiting.')


