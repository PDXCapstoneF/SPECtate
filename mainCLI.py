"""SPECtate.

Usage:
    mainCLI.py run <config> [--props <props>]
    mainCLI.py validate <config>
    mainCLI.py (-h | --help)
    mainCLI.py --version
    mainCLI.py dialogue
"""
# library imports
import json
import os
from subprocess import call
from shutil import copy, rmtree

# external imports
from docopt import docopt

# source imports
import dialogue
from src import validate



def to_list(s):
    if s["run_type"].lower() in ["hbir", "hbir_rt"]:
        return [
                s["run_type"], # RUNTYPE
                s["kit_version"], # kitVersion
                s["tag"], # tag
                s["jdk"], # JDK
                s["rt_start"], # RT curve start
                " ".join(s["jvm_options"]), # JVM options
                s["numa_node"], # NUMA node
                s["data"], # DATA
                s["t"][0], # T1
                s["t"][1], # T2
                s["t"][2], # T3
                ]
    else:
        return [
                s["run_type"], # runtype
                s["kit_version"], # kitversion
                s["tag"], # tag
                s["jdk"], # jdk
                s["rt_start"], # rt curve start
                s["duration"],
                " ".join(s["jvm_options"]), # jvm options
                s["numa_node"], # numa node
                s["data"], # data
                s["t"][0], # t1
                s["t"][1], # t2
                s["t"][2], # t3
                ]

def relative_to_main(relname):
    return os.path.join(os.path.dirname(__file__), relname)

blackbox_artifacts = [
    '.run_number',
    'controller.out',
    'specjbb2015.props',
    'sut.txt',
        ]

def do_run(arguments):
    """
    Does a run using scripts/run.sh from the provided property template and configuration.
    """
    with open(arguments['<config>'], 'r') as f:
        args = json.loads(f.read())
    stringified = list(map(lambda arg: str(arg), to_list(args['specjbb'])))
    workdir = args['specjbb'].get('workdir', 'scripts')
    scripts_abspath = relative_to_main(workdir)
    workdir_abspath = relative_to_main('scripts')

    # if we don't already have the scripts available to us
    # copy them into the new location
    if workdir != 'scripts':
        copy(scripts_abspath, workdir_abspath)

    def cleanup():
        # we need to cleanup the cwd or worktree for some reason
        if workdir != 'scripts':
            rmtree(workdir_abspath)
        else:
            for name in map(lambda name: os.path.join(scripts_abspath, name), 
                blackbox_artifacts):
                os.remove(name)

    try:
        if not call(['bash', 'run.sh'] + stringified, cwd=workdir_abspath):
            cleanup()
    except:
        cleanup()


def do_validate(arguments):
    """
    Validate a configuration based on the schema provided.
    """
    with open(arguments['<config>'], 'r') as f:
        args = json.loads(f.read())
    return validate.validate(args) is None

def do_dialogue(arguments):
    dialogue.dialogue()

# dictionary of runnables
# these are functions that take arguments from the
# command line and do something with them.
do = {
        'run': do_run,
        'validate': do_validate,
        'dialogue' : do_dialogue
        }


if __name__ == "__main__":
    arguments = docopt(__doc__, version='SPECtate v0.1')

    for key, func in do.items():
        if arguments[key]:
            r = func(arguments)

            if r is not None:
                exit(r)
