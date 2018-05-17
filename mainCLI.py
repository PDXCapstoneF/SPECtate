"""SPECtate.

Usage:
    mainCLI.py run [options] <config> [--props <props>]
    mainCLI.py validate [options] <config>
    mainCLI.py compliant [options] <config>
    mainCLI.py dialogue [options]
    mainCLI.py script [options] <script> [ARG ...]
    mainCLI.py scripts [options]
    mainCLI.py (-h | --help)
    mainCLI.py --version

Options:
    --level=<log-level>       Set the logging level. Uses python.logging's names for the different leves. [default: INFO]
"""
# library imports
import json
import os
from os.path import dirname, join
import logging
import sys
from subprocess import call
from shutil import copy, rmtree

# external imports
from docopt import docopt

# source imports
import dialogue
from src import validate
from src import run_generator
from src import benchmark_run

log = logging.getLogger(__name__)

def to_list(s):
    if s["run_type"].lower() in ["hbir", "hbir_rt"]:
        return [
            s["run_type"],  # RUNTYPE
            s["kit_version"],  # kitVersion
            s["tag"],  # tag
            s["jdk"],  # JDK
            s["rt_start"],  # RT curve start
            " ".join(s["jvm_options"]),  # JVM options
            s["numa_node"],  # NUMA node
            s["data"],  # DATA
            s["t"][0],  # T1
            s["t"][1],  # T2
            s["t"][2],  # T3
        ]
    else:
        return [
            s["run_type"],  # runtype
            s["kit_version"],  # kitversion
            s["tag"],  # tag
            s["jdk"],  # jdk
            s["rt_start"],  # rt curve start
            s["duration"],
            " ".join(s["jvm_options"]),  # jvm options
            s["numa_node"],  # numa node
            s["data"],  # data
            s["t"][0],  # t1
            s["t"][1],  # t2
            s["t"][2],  # t3
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

    try:
        if validate.validate_blackbox(args) is not None:
            return
    except Exception as e:
        print(e)

    print("attempting to validate SPECtate configuration...")

    try:
        return validate.validate(args) is None
    except Exception as e:
        return e
    return True


def do_dialogue(arguments):
    dialogue.dialogue()


def do_run(arguments):
    with open(arguments['<config>'], 'r') as f:
        args = json.loads(f.read())
    rs = run_generator.RunGenerator(**args)
    for r in rs.runs:
        s = benchmark_run.SpecJBBRun(**r)

        s.run()

def do_script(arguments):
    call(["perl", "scripts/{}.pl".format(arguments["<script>"])] + arguments["ARG"])

def do_scripts(arguments):
    log.info("These are the scripts available to run using 'script':")
    log.info([script for script in os.listdir(join(dirname(__file__), "scripts")) if script.endswith("pl")])

def do_compliant(arguments):
    with open(arguments['<config>'], 'r') as f:
        args = json.loads(f.read())
    rs = run_generator.RunGenerator(**args)
    for r in rs.runs:
        s = benchmark_run.SpecJBBRun(**r)

        log.info("validating the following run:")
        s.dump(logging.INFO)
        log.info("compliant? {}".format(s.compliant()))


# dictionary of runnables
# these are functions that take arguments from the
# command line and do something with them.
do = {
    'run': do_run,
    'validate': do_validate,
    'compliant': do_compliant,
    'dialogue': do_dialogue,
    'script': do_script,
    'scripts': do_scripts,
}

if __name__ == "__main__":
    arguments = docopt(__doc__, version='SPECtate v0.1')
    logging.basicConfig(level=logging.getLevelName(arguments['--level']))

    for key, func in do.items():
        if arguments[key]:
            r = func(arguments)

            if not r or r is not None:
                sys.exit(r)
