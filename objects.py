import copy
import datetime
import json
import multiprocessing
import os
import shlex
import shutil
import signal
import time
from subprocess import Popen, PIPE, STDOUT

from src.stream import stream


class spec_config:
    # runs contains a list of spec_run's
    def __init__(self, fromjson=None):
        self.runs = []
        self.type = "spec_config"
        self.spec_dir = ""
        if not fromjson is None:
            for r in fromjson.get('runs', []):
                self.runs.append(spec_run(r))

    def switch_type(self):
        if self.type == "spec_config":
            self.type = "tate_config"
        else:
            self.type = "spec_config"

    def run(self, outhandle, errhandle):
        """

        :param path: The path to a directory containing specjbb.jar
        :param outhandle: A function to handle std output
        :param errhandle: A function to handle std error
        :return:
        """
        if not self.runs:
            return 0
        jar_path = self.runs[0].spec_dir
        if jar_path == "":
            jar_path = os.getcwd()
        jar_file = os.path.join(jar_path, "specjbb2015.jar")
        if not os.path.exists(jar_file):
            errhandle('Failed to locate "specjbb2015.jar" in "{}"'.format(jar_path))
            return 2
        result_dir = "{}/results_{}-runs_{}".format(jar_path, len(self.runs),
                                                    datetime.datetime.fromtimestamp(time.time()).strftime(
                                                        '+%y-%m-%d_%H%M%S'))
        os.makedirs(result_dir)
        for r in self.runs:
            result = r._run(jar_file, result_dir, outhandle, errhandle)
            if result != 0:
                return result
        self._rollup(result_dir, outhandle)
        return 0

    def set_spec_dir(self, path):
        for r in self.runs:
            r.spec_dir = path


    def _rollup(self, path: str, outhandle):
        """
        :param path: Path to a directory containing directories of results
        :return: The path to the result .csv file
        """
        if not os.path.exists(path):
            raise FileNotFoundError(path)
        rollscript = os.path.abspath(os.path.join(__file__, os.pardir))
        rollscript = os.path.join(rollscript, "scripts", "Rollup.pl")
        if not os.path.exists(rollscript):
            raise FileNotFoundError(rollscript)
        perlbin = '/usr/bin/perl'
        if not os.path.exists(perlbin):
            perlbin = '/bin/perl'
            if not os.path.exists(perlbin):
                return
        outhandle(os.linesep)
        outhandle(os.linesep)
        outhandle("Starting analysis on {}...".format(path))
        outhandle(os.linesep)
        p = Popen(shlex.split("{} {} {}".format(perlbin, rollscript, path)), cwd=path, stdout=PIPE, stderr=STDOUT,
                  universal_newlines=True)
        outstream = stream(p.stdout)
        while p.poll() is None:
            o = outstream.readline()
            if o != '':
                outhandle(o)
        p.wait()
        resname, resext = os.path.splitext(os.path.basename(path))
        resname += ".csv"
        result = os.path.join(os.path.abspath(os.path.join(path, os.pardir)), resname)
        return result

    def _tojson(self):
        """Returns dictionary of json terms.  Should only be called internally"""
        if self.type == "spec_config":
            return {
                "_type": "spec_config",
                "runs": list(map(lambda x: x._tojson(), self.runs))
            }
        else:
            return self._totateconfig()

    def _totateconfig(self):
        return {
            "TemplateData": {"CURSES": {
                "args": [
                    "JDK",
                    "JVM Options",
                    "Run Type",
                    "Tag",
                    "Numa Nodes",
                    "Verbose",
                    "Report Level",
                    "Skip Report",
                    "Ignore Kit Validation",
                    "Number of Runs",
                    "Data Collection"
                ],
                "annotations": {
                    "JDK": "The full path location of a java executable to be invoked",
                    "JVM Options": "A string of arguments to be passed to the JVM",
                    "Run Type": "The run type must be 'composite', 'distributed_ctrl_txl', 'distributed_sut', or 'multi'",
                    "Tag": "The name of this run",
                    "Numa Nodes": "The number of numa nodes to use when running multiple TXINJECTOR's or BACKEND's",
                    "Verbose": "Whether or not SPECjbb will produce verbose output during a run",
                    "Skip Report": "Whether or not SPECjbb will skip producing a report after completion",
                    "Ignore Kit Validation": "Whether or not SPECjbb will perform kit validation prior to running",
                    "Number of Runs": "The number of times this run will execute sequentially",
                    "Data Collection": "Currently unsupported"
                },
                "types": {
                    "JDK": "string",
                    "JVM Options": "string",
                    "Run Type": "string",
                    "Tag": "string",
                    "Numa Nodes": "integer",
                    "Verbose": "boolean",
                    "Skip Report": "boolean",
                    "Ignore Kit Validation": "boolean",
                    "Number of Runs": "integer",
                    "Data Collection": "string"
                }
            }},
            "RunList": list(map(lambda x: x._totateconfig(), self.runs))
        }

    def save(self, path: str):
        """Call this to save this config to a json file."""
        with open(path, 'w') as f:
            json.dump(self, f, indent=4, cls=spec_encoder)


class spec_encoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, spec_config) or isinstance(obj, spec_run) or isinstance(obj, props) or isinstance(obj,
                                                                                                             propitem):
            return obj._tojson()
        return super(spec_encoder, self).default(obj)


class spec_decoder(json.JSONDecoder):
    def __init__(self, *args, **kwargs):
        json.JSONDecoder.__init__(
            self, object_hook=self.object_hook, *args, **kwargs)

    def object_hook(self, obj):
        type = obj.get('_type', '')
        if type == 'spec_config':
            return spec_config(obj)
        templates = obj.get('TemplateData', '')
        if templates != '':
            return self.decode_tate(obj, templates)
        return obj

    def decode_tate(self, obj, templates):
        runlist = obj.get('RunList', '')
        if runlist == '':
            raise AssertionError("Json file has no run lists")
        # Run lists is a list, templates is a dict.
        ret = spec_config()
        ret.type = "tate_config"
        for run in runlist:
            r = spec_run()
            template_type = run.get('template_type', '')
            if template_type == '':
                raise AssertionError("Run in RunList has no template type")
            temp = templates.get(template_type, '')
            if temp == '':
                raise AssertionError("Template '{}' does not exist in TemplateData".format(temp))
            translations = temp.get('translations', {})
            for k, v in run.items():
                if k in known_args:
                    r._set_known_arg(k, v)
                    continue
                t = translations.get(k, '')
                if t != '':
                    r._set_by_translation(t, v)
            extra = run.get('props_extra', [])
            for d in extra:
                name = d.get('prop', '')
                value = d.get('value', '')
                r.properties.set(name, value)
            ret.runs.append(r)
        return ret


class spec_run:
    _running = False

    def __init__(self, fromjson=None):
        if fromjson is None:
            self.properties = props()
            self.jdk = "/usr/bin/java"
            self.jvm_options = "-Xms29g -Xmx29g -Xmn27g -XX:ParallelGCThreads=48"
            self.data_collection = "NONE"
            self.num_runs = 1
            self.numa_nodes = 1
            self.tag = "tag-name"
            # must be 'multi, 'distributed_ctrl_txl', 'distributed_sut', 'multi'
            self.run_type = 'composite'
            self.verbose = False
            self.report_level = 0  # must be between 0-3
            self.skip_report = False
            self.ignore_kit_validation = False
            self.spec_dir = ""
        else:
            self.jdk = fromjson.get('jdk', "/usr/bin/java")
            self.jvm_options = fromjson.get('jvm_options', "-Xms29g -Xmx29g -Xmn27g -XX:ParallelGCThreads=48")
            self.data_collection = fromjson.get('data_collection', "NONE")
            self.num_runs = fromjson.get('num_runs', 1)
            self.tag = fromjson.get('tag', "tag-name")
            self.run_type = fromjson.get('run_type', 'composite')
            self.properties = props(fromjson.get('props', {"modified": []}))
            self.verbose = fromjson.get('verbose', False)
            self.numa_nodes = fromjson.get('numa_nodes', 1)
            self.report_level = fromjson.get('report_level', 0)
            self.skip_report = fromjson.get('skip_report', False)
            self.ignore_kit_validation = fromjson.get('ignore_kit_validation', False)
            self.spec_dir = fromjson.get('spec_dir', "")

    def set_runtype(self, arg: str):
        """Ensure that arg is a valid runtype before setting the runtype"""
        if arg in run_types:
            self.run_type = arg

    def get_help(self, arg: str):
        """
        Gets a description of any spec_run member variable
        :param arg: The string name of one of spec_run's member variables
        :return: A string description of the variable
        """
        if arg == "properties":
            return "A list of SPECjbb configuration properties"
        if arg == "jvm_options":
            return "A string of valid JVM command line arguments"
        if arg == "data_collection":
            return "A list of commands, separated by ';' that will be run and logged during each run."
        if arg == "num_runs":
            return "The number of times to repeat this run"
        if arg == "tag":
            return "A unique name identifying this run"
        if arg == "run_type":
            return "Method of running SPECjbb.  (Composite = single run on a single machine.  " \
                   "Multi = single run using multiple JVMS on a single machine.  " \
                   "Distributed = single run on multiple machines"
        if arg == "verbose":
            return "Be verbose"
        if arg == "report_level":
            return "Report level (0 = bare minimum, 3 = every single thing) (default: 0)"
        if arg == "skip_report":
            return "Skip report generation at the end of run"
        if arg == "ignore_kit_validation":
            return "Ignore kit validation"
        return "Unknown option"

    def _set_known_arg(self, key: str, value):
        if key == 'JDK':
            self.jdk = value
        elif key == 'JVM Options':
            self.jvm_options = value
        elif key == 'Run Type':
            self.run_type = value
        elif key == 'Tag':
            self.tag = value
        elif key == 'Verbose':
            self.verbose = value
        elif key == 'Numa Nodes':
            self.numa_nodes = value
        elif key == 'Skip Report':
            self.skip_report = value
        elif key == 'Ignore Kit Validatio':
            self.ignore_kit_validation = value
        elif key == 'Number of Runs':
            self.num_runs = value
        elif key == 'Data Collection':
            self.data_collection = value

    def _set_by_translation(self, trans, value):
        self.properties.set(trans, value)

    def _tojson(self):
        """Returns dictionary of json terms.  Should only be called internally"""
        return {
            "jdk": self.jdk,
            "jvm_options": self.jvm_options,
            "data_collection": self.data_collection,
            "num_runs": self.num_runs,
            "run_type": self.run_type,
            "tag": self.tag,
            "numa_nodes": self.numa_nodes,
            "verbose": self.verbose,
            "report_level": self.report_level,
            "skip_report": self.skip_report,
            "ignore_kit_validation": self.ignore_kit_validation,
            "props": self.properties._tojson(),
            "spec_dir": self.spec_dir
        }

    def _totateconfig(self):
        return {
            "template_type": "CURSES",
            "JDK": self.jdk,
            "JVM Options": self.jvm_options,
            "Run Type": self.run_type,
            "Tag": self.tag,
            "Numa Nodes": self.numa_nodes,
            "Verbose": self.verbose,
            "Report Level": self.report_level,
            "Skip Report": self.skip_report,
            "Ignore Kit Validation": self.ignore_kit_validation,
            "Number of Runs": self.num_runs,
            "Data Collection": self.data_collection,
            "props_extra": self.properties._totateconfig()
        }

    def _defHandle(msg):
        print(msg)

    # handle = Any function that takes a single string argument.
    # It can be used to intercept any output
    # If set to None, then output will only be logged
    def _run(self, jar_file="", result_path="", handle_out=_defHandle, handle_err=_defHandle):
        """
        Runs with the current settings.  Auto detects runtype, writes the config file, and executes all required processes
        :param path: The path to a directory containing 'specjbb2015.jar'
        :param handle: An output handler.  Will receive byte encoded strings?
                    If left blank, all output will be 'printed'
        :return: 0 -> All runs completed successfully
                 2 -> Failed to located 'specjbb2015.jar' in the path
                 3 -> Java executable not found
                 4 -> Failed to ping the host controller
                -1 -> An error ocurred executing specjbb
        """
        if not os.path.exists(self.jdk):
            return 3
        fname, fext = os.path.splitext(jar_file)
        if not os.path.exists(jar_file) or fext != '.jar':
            handle_err('Failed to locate "specjbb2015.jar" in "{}"'.format(jar_file))
            return 2

        if result_path == "" or not os.path.exists(result_path):
            result_path = os.path.abspath(os.path.join(jar_file, os.pardir))
        switch = {
            'composite': self._run_composite,
            'distributed_ctrl_txl': self._run_distributed_ctrl_txl,
            'distributed_sut': self._distributed_sut,
            'multi': self._run_multi
        }
        orig_sig = signal.getsignal(signal.SIGINT)
        spec_run._running = True
        signal.signal(signal.SIGINT, spec_run._signal_handler)

        ret = switch[self.run_type](jar_file, result_path, handle_out, handle_err)

        signal.signal(signal.SIGINT, orig_sig)
        spec_run._running = False
        return ret

    def _run_composite(self, jar: str, result_parent: str, handle_out, handle_err):
        """Called internally only by this.run()"""
        cmd = '{} {} -jar {} -m COMPOSITE {}'.format(
            self.jdk, self.jvm_options, jar, self._spec_opts())

        for x in range(int(self.num_runs)):
            result_dir = self._prerun(result_parent)
            handle_out(os.linesep)
            handle_out(os.linesep)
            handle_out('Starting run {} of {}.'.format(x, self.num_runs))
            handle_out('Using command: "{}"'.format(cmd))
            handle_out(os.linesep)
            handle_out(os.linesep)
            data = self._start_data_collection(result_dir, handle_out)
            errout = open(os.path.join(result_dir, 'composite.out'), 'w')
            stdout = open(os.path.join(result_dir, 'composite.log'), 'w')
            p = Popen(shlex.split(cmd), cwd=result_dir, stdout=PIPE, stderr=PIPE, universal_newlines=True)
            spec_run._running = True
            errstream = stream(p.stderr)
            outstream = stream(p.stdout)
            while spec_run._running and p.poll() is None:
                e = errstream.readline()
                if e != '':
                    errout.write(e)
                    handle_err(e)
                o = outstream.readline()
                if o != '':
                    stdout.write(o)
                    handle_out(o)
            errout.close()
            errstream.close()
            stdout.close()
            outstream.close()
            if spec_run._running:
                exitcode = p.wait()
            else:
                handle_out(os.linesep)
                handle_out(os.linesep)
                handle_out("Canceling benchmark...")
                exitcode = 0
                p.kill()
            for pf in data:
                pf.kill()
            if exitcode != 0 and spec_run._running:
                return -1
        return 0

    def _run_distributed_ctrl_txl(self, jar: str, result_parent: str, handle_out, handle_err):
        """Called internally only by this.run()"""
        ctrl_ip = self.properties.root['specjbb.controller.host'].value
        pingcmd = 'ping -c 1 {}'.format(ctrl_ip)
        handle_out(os.linesep)
        handle_out(os.linesep)
        handle_out("Checking host {} is online...".format(ctrl_ip))
        FNULL = open(os.devnull, 'w')
        ping = Popen(shlex.split(pingcmd), stderr=FNULL, stdout=FNULL)
        exitcode = ping.wait()
        FNULL.close()
        if exitcode != 0:
            handle_err('ERROR: Failed to ping Controller host (specjbb.controller.host): {}'.format(ctrl_ip))

            return 4
        handle_out(os.linesep)
        handle_out(os.linesep)
        handle_out("Starting injectors, press Ctrl + C to terminate run.")
        handle_out(os.linesep)
        opts = self._spec_opts()
        tx_opts = self._tx_opts()
        result_dir = self._prerun(result_parent)
        cmd = '{} {} -jar {} -m DISTCONTROLLER {}'.format(self.jdk, self.jvm_options, jar, opts)
        tx_procs = []
        cont_std = open(os.path.join(result_dir, 'controller.log'), 'w')
        cont_err = open(os.path.join(result_dir, 'controller.out'), 'w')
        controller = Popen(shlex.split(cmd), cwd=result_dir, stdout=PIPE, stderr=PIPE, universal_newlines=True)
        data = self._start_data_collection(result_dir, handle_out)
        for g in range(int(self.properties.root['specjbb.group.count'].value)):
            for j in range(int(self.properties.root['specjbb.txi.pergroup.count'].value)):
                ti_name = "{}Group{}.TxInjector.txiJVM{}".format(result_dir, g, j)
                cmd = '{} {} -jar {} -m TXINJECTOR -G={}'.format(self.jdk, self.jvm_options, jar,
                                                                 tx_opts, g)
                p = Popen(shlex.split(cmd), cwd=result_dir, stdout=PIPE, stderr=PIPE, universal_newlines=True)
                tx_procs.append([p,
                                 open(os.path.join(result_dir, '{}.log'.format(ti_name)), 'w'),
                                 open(os.path.join(result_dir, '{}.out'.format(ti_name)), 'w'),
                                 stream(p.stderr),
                                 stream(p.stdout)])
        spec_run._running = True
        errstream = stream(controller.stderr)
        outstream = stream(controller.stdout)
        while spec_run._running and controller.poll() is None:
            e = errstream.readline()
            if e != '':
                cont_err.write(e)
                handle_err(e)
            o = outstream.readline()
            if o != '':
                cont_std.write(o)
                handle_out(o)
            for p in tx_procs:
                if p[0].poll() is None:
                    e = p[3].readline()
                    if e != '':
                        p[2].write(e)
                        handle_err(e)
                    o = p[4].readline()
                    if o != '':
                        p[1].write(o)
                        handle_out(o)
        cont_err.close()
        cont_std.close()
        if spec_run._running:
            exitcode = controller.wait()
        else:
            handle_out(os.linesep)
            handle_out("Ending benchmark...")
            exitcode = 0
            controller.kill()
        for p in tx_procs:
            p[3].close()
            p[4].close()
            p[0].kill()
            p[1].close()
            p[2].close()
        for pf in data:
            pf.kill()
        if exitcode != 0 and spec_run._running:
            return -1
        return 0

    def _distributed_sut(self, jar: str, result_parent: str, handle_out, handle_err):
        """Called internally only by this.run()"""
        ctrl_ip = self.properties.root['specjbb.controller.host'].value
        pingcmd = 'ping -c 1 {}'.format(ctrl_ip)
        handle_out(os.linesep)
        handle_out(os.linesep)
        handle_out("Checking host {} is online...".format(ctrl_ip))
        FNULL = open(os.devnull, 'w')
        ping = Popen(shlex.split(pingcmd), stderr=FNULL, stdout=FNULL)
        exitcode = ping.wait()
        FNULL.close()
        if exitcode != 0:
            handle_err('ERROR: Failed to ping Controller host (specjbb.controller.host): {}'.format(ctrl_ip))
            return 4
        handle_out(os.linesep)
        handle_out("Starting backends, press Ctrl + C to terminate.")
        handle_out(os.linesep)
        opts = self._tx_opts()
        procs = []
        result_dir = self._prerun(result_parent)
        data = self._start_data_collection(result_dir, handle_out)
        for g in range(int(self.properties.root['specjbb.group.count'].value)):
            be_name = 'beJVM Group{}.Backend.beJVM.log'.format(g)
            cmd = '{} {} -jar {} -m BACKEND {} -G={} -J=beJVM'.format(self.jdk, self.jvm_options, jar,
                                                                      opts, g)
            p = Popen(shlex.split(cmd), cwd=result_dir, stdout=PIPE, stderr=STDOUT, universal_newlines=True)
            procs.append([p,
                          open(os.path.join(result_dir, be_name), 'w'),
                          stream(p.stdout)])

        spec_run._running = True
        while spec_run._running:
            for p in procs:
                if p[0].poll() is None:
                    o = p[2].readline()
                    if o != '':
                        handle_out(o)
                        p[1].write(o)
        for p in procs:
            p[2].close()
            p[0].kill()
            p[1].close()
        for pf in data:
            pf.kill()
        # Each process will continue until manually terminated with ctrl c.
        return 0

    def _run_multi(self, jar: str, result_parent: str, handle_out, handle_err):
        """Called internally only by this.run()"""

        opts = self._spec_opts()
        tx_opts = self._tx_opts()
        has_numa = self._check_numa() and self.numa_nodes > 1
        numa_cmd = 'numactl --cpunodebind={} --localalloc'
        for x in range(int(self.num_runs)):
            handle_out(os.linesep)
            result_dir = self._prerun(result_parent)
            handle_out("Starting run {} of {} in {}...".format(x +
                                                               1, self.num_runs, result_dir))
            handle_out(os.linesep)
            handle_out(os.linesep)

            cont_std = open(os.path.join(result_dir, 'controller.log'), 'w')
            cont_err = open(os.path.join(result_dir, 'controller.out'), 'w')
            cmd = '{} {} -jar {} -m MULTICONTROLLER {}'.format(self.jdk, self.jvm_options, jar, opts)
            controller = Popen(shlex.split(cmd), cwd=result_dir, stdout=PIPE, stderr=PIPE, universal_newlines=True)
            tx_procs = []
            be_procs = []
            data = self._start_data_collection(result_dir, handle_out)
            for g in range(int(self.properties.root['specjbb.group.count'].value)):
                numa = numa_cmd.format((g - 1) % 4)
                for j in range(self.properties.root['specjbb.txi.pergroup.count'].value):
                    ti_name = "Group{}.TxInjector.txiJVM{}".format(g, j)
                    if has_numa:
                        cmd = '{} {} {} -jar {} -m TXINJECTOR -G={} -J=txiJVM{} {}'.format(numa, self.jdk,
                                                                                           self.jvm_options,
                                                                                           jar, g, j,
                                                                                           tx_opts)
                    else:
                        cmd = '{} {} -jar {} -m TXINJECTOR -G={} -J=txiJVM{} {}'.format(self.jdk, self.jvm_options,
                                                                                        jar, g, j, tx_opts)
                    handle_out('Using command: "{}"'.format(cmd))
                    p = Popen(shlex.split(cmd), cwd=result_dir, stdout=PIPE, stderr=PIPE, universal_newlines=True)
                    tx_procs.append([p,
                                     open(os.path.join(result_dir, '{}.log'.format(ti_name)), 'w'),
                                     open(os.path.join(result_dir, '{}.out'.format(ti_name)), 'w'),
                                     stream(p.stderr),
                                     stream(p.stdout)])
                be_name = "Group{}.Backend.beJVM".format(g)
                if has_numa:
                    cmd = '{} {} {} -jar {} -m BACKEND {} -G={} -J=beJVM'.format(numa, self.jdk,
                                                                                 self.jvm_options,
                                                                                 jar, tx_opts,
                                                                                 g)
                else:
                    cmd = '{} {} -jar {} -m BACKEND {} -G={} -J=beJVM'.format(self.jdk, self.jvm_options,
                                                                              jar, tx_opts,
                                                                              g)
                handle_out('Using command: "{}"'.format(cmd))
                p = Popen(shlex.split(cmd), cwd=result_dir, stdout=PIPE, stderr=PIPE, universal_newlines=True)
                be_procs.append([p,
                                 open(os.path.join(result_dir, '{}.log'.format(be_name)), 'w'),
                                 open(os.path.join(result_dir, '{}.out'.format(be_name)), 'w'),
                                 stream(p.stderr),
                                 stream(p.stdout)])

            spec_run._running = True
            errstream = stream(controller.stderr)
            outstream = stream(controller.stdout)
            while spec_run._running and controller.poll() is None:
                e = errstream.readline()
                if e != '':
                    cont_err.write(e)
                    handle_err(e)
                o = outstream.readline()
                if o != '':
                    cont_std.write(o)
                    handle_out("Controller: {}".format(o))
                for p in tx_procs:
                    if not spec_run._running:
                        break
                    if p[0].poll() is None:
                        e = p[3].readline()
                        if e != '':
                            p[2].write(e)
                            handle_err(e)
                        o = p[4].readline()
                        if o != '':
                            p[1].write(o)
                            handle_out("TX: {}".format(o))
                for p in be_procs:
                    if not spec_run._running:
                        break
                    if p[0].poll() is None:
                        e = p[3].readline()
                        if e != '':
                            p[2].write(e)
                            handle_err(e)
                        o = p[4].readline()
                        if o != '':
                            p[1].write(o)
            handle_out(os.linesep)
            handle_out("Benchmark {} of {} ended.".format(x + 1, self.num_runs))
            cont_err.close()
            cont_std.close()
            if spec_run._running:
                exitcode = controller.wait()
            else:
                handle_out(os.linesep)
                handle_out("Canceling benchmark...")
                handle_out(os.linesep)
                exitcode = 0
                controller.kill()
            for p in tx_procs:
                p[3].close()
                p[4].close()
                p[0].kill()
                p[1].close()
                p[2].close()
            for p in be_procs:
                p[3].close()
                p[4].close()
                p[0].kill()
                p[1].close()
                p[2].close()
            for pf in data:
                pf.kill()
            if exitcode != 0 and spec_run._running:
                return -1
        return 0

    def _prerun(self, path: str):
        """
        Called internally only.  Builds a result directory and writes the current config to it.
        :param path: Path to results folder
        :return:
        """
        result_dir = "{}/{}-{}".format(path, datetime.datetime.fromtimestamp(time.time()).strftime('+%y-%m-%d_%H%M%S'),
                                       self.tag)
        os.makedirs(result_dir)
        if not os.path.exists("{}/config".format(result_dir)):
            os.makedirs("{}/config".format(result_dir))
        self.properties.writeconfig("{}/config/specjbb2015.props".format(result_dir))
        templates = os.path.abspath(os.path.join(__file__, os.pardir))
        templateC = os.path.join(templates, "scripts", "template-C.raw")
        templateD = os.path.join(templates, "scripts", "template-D.raw")
        templateM = os.path.join(templates, "scripts", "template-M.raw")
        shutil.copyfile(templateC, os.path.join(result_dir, "config", "tempalte-C.raw"))
        shutil.copyfile(templateD, os.path.join(result_dir, "config", "tempalte-D.raw"))
        shutil.copyfile(templateM, os.path.join(result_dir, "config", "tempalte-M.raw"))
        return result_dir

    def _start_data_collection(self, results_dir: str, handle):
        procs = []
        cmds = self.data_collection.split(";")
        for c in cmds:
            if c != 'NONE' and c != '':
                shcmd = shlex.split(c)
                if os.path.exists(shcmd[0]) or any(os.access(os.path.join(path, shcmd[0]), os.X_OK) for path in os.environ["PATH"].split(os.pathsep)):
                    handle("Starting data collection ''{}".format(c))
                    stdout = open(os.path.join(results_dir, "{}.log".format(shcmd[0])), 'w')
                    procs.append(Popen(shcmd, cwd=results_dir, stdout=stdout, stderr=STDOUT, close_fds=True,
                                       universal_newlines=True))
                else:
                    handle("Failed to start data collection: '{}', command does not exit".format(c))
        return procs

    def _tx_opts(self):
        """Called internally only.  Obtains specjbb options available to TXINJECTOR and BACKEND"""
        opts = ""
        if self.verbose:
            opts += " -v"
        if self.ignore_kit_validation:
            opts += " -ikv"
        return opts

    def _spec_opts(self):
        """Called internally only.  Obtains specjbb options available to all except TXINJECTOR and BACKEND"""
        opts = "-l {}".format(self.report_level)
        if self.skip_report:
            opts += " -skipReport"
        if self.verbose:
            opts += " -v"
        if self.ignore_kit_validation:
            opts += " -ikv"
        return opts

    def _check_numa(self):
        p = Popen(shlex.split('which numactl'), stdout=PIPE)
        o, e = p.communicate()
        result = len(o) > 0
        p.wait()
        return result

    @staticmethod
    def _signal_handler(signum, frame):
        if spec_run._running:
            spec_run._running = False
        signal.signal(signal.SIGINT, spec_run._signal_handler)


class propitem:
    def __init__(self, prop, def_value, desc, input_validator, value_validator, valid_opts=None, help_text=""):
        self.prop = prop
        self.def_value = def_value
        self.desc = desc
        self.input_validator = input_validator
        self.value_validator = value_validator
        self.help_text = help_text
        if valid_opts is None:
            self.valid_opts = []
        else:
            self.valid_opts = valid_opts
        self.value = def_value

    def _write(self, f):
        """Called internally only.  Writes to a config file if different than the default value"""
        if self.value != self.def_value:
            f.write("{} = {}".format(self.prop, self.value))

    def set(self, arg):
        """Use this to set this property value using a validator"""
        if self.value_validator(arg):
            self.value = arg

    def reset(self):
        """Resets this property to the default value"""
        self.value = self.def_value

    def _totateconfig(self):
        return self._tojson()

    def _tojson(self):
        """Called internally only.  Returns dictionary of json values"""
        return {
            "prop": self.prop,
            "value": self.value
        }


known_args = [
    'JDK',
    'JVM Options',
    'Run Type',
    'Tag',
    'Numa Nodes',
    'Verbose',
    'Skip Report',
    'Ignore Kit Validation',
    'Number of Runs',
    'Data Collection'
]

run_types = [
    'composite',
    'distributed_ctrl_txl',
    'distributed_sut',
    'multi'
]

loglevels = [
    'SEVERE',
    'WARNING',
    'INFO',
    'CONFIG',
    'FINE',
    'FINER',
    'FINEST'
]

con_types = [
    'HBIR_RT',
    'HBIR',
    'PRESET',
    'FIXED_RT',
    'FIXED_RT_LOADLEVELS',
    'FIXED_LOADLEVELS'
]

must_be_positive = "Value must be greater than 0"


def number_validator(x): return int(x) <= ord('9') and int(x) >= ord('0')


def float_validator(x): return (
    x <= ord('9') and x >= ord('0')) or x == ord('.')


def default_validator(x): return True


defaults = [
    propitem('specjbb.controller.type', 'HBIR_RT', 'Controls phases being controlled by Controller.', default_validator,
             lambda x: x in con_types, con_types),
    propitem('specjbb.comm.connect.client.pool.size', 256,
             'Network connection pool size, i.e. number of sockets for I/O communication for each Agent.',
             number_validator, lambda x: int(x) > 0, help_text=must_be_positive),
    propitem('specjbb.comm.connect.worker.pool.min', 1,
             'Minimum number of worker threads in the network connection pool.',
             number_validator, lambda x: int(x) > 0, help_text=must_be_positive),
    propitem('specjbb.comm.connect.worker.pool.max', 256,
             'Maximum number of worker threads in the network connection pool.',
             number_validator, lambda x: int(x) > 0, help_text=must_be_positive),
    propitem('specjbb.comm.connect.selector.runner.count', 0,
             'Number of acceptor threads for handling new connections and scheduling existing ones.',
             number_validator, lambda x: int(x) >= 0,
             help_text="Value must an integer. Special '0' value  will force to using the default connectivity provider setting"),
    propitem('specjbb.comm.connect.timeouts.connect', 60000, 'Timeout (in milliseconds) for I/O connection operation.',
             number_validator, lambda x: int(x) > 0, help_text=must_be_positive),
    propitem('specjbb.comm.connect.timeouts.read', 60000, 'Timeout (in milliseconds) for I/O read operation.',
             number_validator, lambda x: int(x) > 0, help_text=must_be_positive),
    propitem('specjbb.comm.connect.timeouts.write', 60000, 'Timeout (in milliseconds) for I/O write operation.',
             number_validator, lambda x: int(x) > 0, help_text=must_be_positive),

    propitem('specjbb.controller.host', "localhost",
             'IP address / host name of the machine where Controller program will be launched.',
             default_validator, default_validator, help_text=must_be_positive),
    propitem('specjbb.controller.port', 24000, 'The network port to which Controller listener will bind.',
             number_validator, lambda x: int(x) > 0, help_text=must_be_positive),

    propitem('specjbb.controller.handshake.period', 5000,
             'Time period (in milliseconds) for logging status of the initial Controller <-> Agent handshaking.',
             number_validator, lambda x: int(x) > 0, help_text=must_be_positive),
    propitem('specjbb.controller.handshake.timeout', 600000,
             'Timeout (in milliseconds) for initial Controller <-> Agent handshaking.',
             number_validator, lambda x: int(x) > 0, help_text=must_be_positive),
    propitem('specjbb.controller.maxir.maxFailedPoints', 3,
             ' Number of points to try after max-jOPS was found to ensure there are no more passes and max-jOPS value is correct.',
             number_validator, lambda x: int(x) >= 0, help_text="Value must be greater than or equal to 0"),

    propitem('specjbb.controller.preset.ir', 1000, 'Sets IR for preset for controller type ',
             number_validator, lambda x: x >= 0, help_text="Value must be greater than or equal to 0"),
    propitem('specjbb.controller.preset.duration', 600000,
             'Sets duration in milliseconds for preset for controller type ',
             number_validator, lambda x: int(x) > 0, help_text="Value must be greater than or equal to 0"),

    propitem('specjbb.controller.rtcurve.duration.min', 60000,
             'Sets duration of steady period of RT step level in milliseconds',
             number_validator, lambda x: int(x) > 0, help_text=must_be_positive),
    propitem('specjbb.controller.rtcurve.duration.max', 90000,
             'Sets duration of steady period of RT step level in milliseconds',
             number_validator, lambda x: int(x) > 0, help_text=must_be_positive),
    propitem('specjbb.controller.rtcurve.start', 0, 'Sets the RT start percent',
             number_validator, lambda x: int(x) >= 0 and int(x) <= 100, help_text="Value must be between 0 and 100"),
    propitem('specjbb.controller.rtcurve.step', 0.01, 'Sets the RT step level to a percent',
             float_validator, lambda x: float(x) > 0 and float(x) <= 1,
             help_text="Value must be a decimal greater than 0 and less than or equal to 1"),
    propitem('specjbb.controller.rtcurve.warmup.step', 0.1,
             'Injection rate for warming up before response-time curve building defined as the percent of the high-bound.',
             float_validator, lambda x: float(x) > 0 and float(x) <= 1,
             help_text="Value must be a decimal greater than 0 and less than or equal to 1"),

    propitem('specjbb.controller.settle.time.min', 3000,
             'Sets duration of settle period of RT step level in milliseconds', number_validator, lambda x: int(
                 x) > 0,
             help_text=must_be_positive),
    propitem('specjbb.controller.settle.time.max', 30000,
             'Sets duration of settle period of RT step level in milliseconds', number_validator, lambda x: int(
                 x) > 0,
             help_text=must_be_positive),

    # propitem('specjbb.customerDriver.threads', 64, 'Maximum number of threads in ThreadPoolExecutor for all three probe/saturate/service requests on the TxInjector side.', lambda x: isinstance(x, int) and x >= 64,help_text=must_be_positive)
    propitem('specjbb.customerDriver.threads.saturate', 64,
             'Maximum number of threads in ThreadPoolExecutor for saturate requests on the TxInjector side.',
             number_validator, lambda x: int(x) >= 64, help_text="Value must be greater than or equal to 64"),
    propitem('specjbb.customerDriver.threads.probe', 64,
             'Maximum number of threads in ThreadPoolExecutor for probe requests on the TxInjector side.',
             number_validator,
             lambda x: int(x) >= 64, help_text="Value must be greater than or equal to 64"),
    propitem('specjbb.customerDriver.threads.service', 64,
             'Maximum number of threads in ThreadPoolExecutor for service requests on the TxInjector side.',
             number_validator,
             lambda x: int(x) >= 64, help_text="Value must be greater than or equal to 64"),
    # propitem('specjbb.forkjoin.workers', multiprocessing.cpu_count() * 2, 'Maximum number of worker threads in ForkJoinPool in each tier on the Backend side.', lambda x:isinstance(x, int),help_text=must_be_positive)
    propitem('specjbb.forkjoin.workers.Tier1', multiprocessing.cpu_count() * 2,
             'Maximum number of worker threads in ForkJoinPool in tier 1 on the Backend side.',
             number_validator, lambda x: int(x) > 0, help_text=must_be_positive),
    propitem('specjbb.forkjoin.workers.Tier2', multiprocessing.cpu_count() * 2,
             'Maximum number of worker threads in ForkJoinPool in tier 2 on the Backend side.', number_validator,
             lambda x: int(x) > 0, help_text=must_be_positive),
    propitem('specjbb.forkjoin.workers.Tier3', multiprocessing.cpu_count() * 2,
             'Maximum number of worker threads in ForkJoinPool in tier 3 on the Backend side.', number_validator,
             lambda x: int(x) > 0, help_text=must_be_positive),
    propitem('specjbb.group.count', 1, 'Number of Groups for the run, where Group is TxInjector(s) mapped to Backend.',
             number_validator, lambda x: int(x) > 0, help_text=must_be_positive),

    propitem('specjbb.heartbeat.period', 10000,
             'How often (in milliseconds) Controller sends heartbeat message to an Agent checking it is alive',
             number_validator,
             lambda x: int(x) > 0, help_text=must_be_positive),
    propitem('specjbb.heartbeat.threshold', 100000,
             'How much time (in milliseconds) await for heartbeat response from an Agent.', number_validator,
             lambda x: int(x) > 0, help_text=must_be_positive),

    propitem('specjbb.time.server', False, 'Enables Controller communication with Time Server.', default_validator,
             lambda x: x is bool, [False, True]),
    propitem('specjbb.txi.pergroup.count', 1, 'Number of TxInjectors per Backend in one Group.', number_validator,
             lambda x: int(x) > 0, help_text=must_be_positive),

    propitem('specjbb.run.datafile.dir', '.', 'Directory for storing binary log file of the run.', default_validator,
             default_validator, help_text="Enter a directory"),
    propitem('specjbb.mapreducer.pool.size', 2,
             'Controller ForkJoinPool size supporting parallel work of TxInjector/Backend agents.', number_validator,
             lambda x: int(x) > 0, help_text=must_be_positive),

    propitem('specjbb.input.number_customers', 100000, 'Total number of customers', number_validator,
             lambda x: int(x) > 0, help_text=must_be_positive),
    propitem('specjbb.input.number_products', 100000, ' Number of products in each Supermarket', number_validator,
             lambda x: int(x) > 0, help_text=must_be_positive),

    propitem('specjbb.logLevel', 'INFO', 'Log level output',
             default_validator, lambda x: x in loglevels, loglevels),

    propitem('specjbb.time.check.interval', 10000,
             'Time interval (in milliseconds) for periodic time check from Time Server', number_validator,
             lambda x: int(x) > 0, help_text=must_be_positive),
    propitem('specjbb.time.offset.max', 600000,
             'Maximum time offset (in milliseconds) between Controller and Time Server on the benchmark start',
             number_validator, lambda x: int(x) > 0, help_text=must_be_positive)
]

def type_convert(obj):
    if obj == 'True' or obj == 'true' or obj == 'T' or obj == 't': return True
    if obj == 'False' or obj == 'false' or obj == 'F' or obj == 'f':return False
    try:

        return int(obj)
    except ValueError:
        try:

            return float(obj)
        except ValueError:
            return obj


class props:
    def __init__(self, fromjson=None):
        self.root = {a.prop: copy.deepcopy(a) for a in defaults}
        if not fromjson is None:
            for p in fromjson.get('modified', []):
                self.set(p['prop'], p['value'])

    def set(self, key: str, value: object):
        """Can be used to set a specific property to a value using a validator"""
        if key in self.root:
            pset = self.root[key]
            if pset.value_validator(value):
                pset.value = value
            else:
                v = type_convert(value)
                if pset.value_validator(v):
                    pset.value = v
                else:
                    raise TypeError

    def get_all(self):
        """Returns a list of 'propitem's"""
        return list(self.root.values())

    def get_modified(self):
        """Returns a list of modified 'propitem's"""
        return [x for x in list(self.root.values()) if isinstance(x, propitem) and x.value != x.def_value]

    def writeconfig(self, path: str):
        """Called internally only before running any 'spec_run'"""
        with open(path, 'w') as f:
            f.write("#SPECjbb config")
            f.write(os.linesep)
            for p in self.get_modified():
                if isinstance(p, propitem):
                    p._write(f)
                    f.write(os.linesep)

    def _tojson(self):
        """Called internally only.  Returns dictionary of json values"""
        return {
            "modified": list(map(lambda x: x._tojson(), self.get_modified()))
        }

    def _totateconfig(self):
        return list(map(lambda x: x._tojson(), self.get_modified()))
