import json
import multiprocessing
import os
import shlex
import time

import datetime

from subprocess import Popen, PIPE, STDOUT


class spec_config():
    # runs contains a list of spec_run's
    def __init__(self, fromjson=None):
        self.runs = []
        self.type = "spec_config"
        if not fromjson is None:
            for r in fromjson.get('runs', []):
                self.runs.append(spec_run(r))

    def switch_type(self):
        if(self.type == "spec_config"):
            self.type = "tate_config"
        else:
            self.type = "spec_config"

    def tojson(self):
        """Returns dictionary of json terms.  Should only be called internally"""
        if(self.type == "spec_config"):
            return {
                "_type":"spec_config",
                "runs": list(map(lambda x: x.tojson(), self.runs))
            }
        else:
            return self.totateconfig()

    def totateconfig(self):
        return {
            "TemplateData": { "CURSES" : {
                "args" : [
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
                "annotations" : {
                    "JDK" : "The full path location of a java executable to be invoked",
                    "JVM Options" : "A string of arguments to be passed to the JVM",
                    "Run Type" : "The run type must be 'composite', 'distributed_ctrl_txl', 'distributed_sut', or 'multi'",
                    "Tag" : "The name of this run",
                    "Numa Nodes" : "The number of numa nodes to use when running multiple TXINJECTOR's or BACKEND's",
                    "Verbose" : "Whether or not SPECjbb will produce verbose output during a run",
                    "Skip Report" : "Whether or not SPECjbb will skip producing a report after completion",
                    "Ignore Kit Validation" : "Whether or not SPECjbb will perform kit validation prior to running",
                    "Number of Runs" : "The number of times this run will execute sequentially",
                    "Data Collection" : "Currently unsupported"
                },
                "types" : {
                    "JDK" : "string",
                    "JVM Options" : "string",
                    "Run Type" : "string",
                    "Tag" : "string",
                    "Numa Nodes" : "integer",
                    "Verbose" : "boolean",
                    "Skip Report" : "boolean",
                    "Ignore Kit Validation" : "boolean",
                    "Number of Runs" : "integer",
                    "Data Collection" : "string"
                }
            }},
            "RunList" : list(map(lambda x: x.totateconfig(), self.runs))
            }

    def save(self, path):
        """Call this to save this config to a json file."""
        with open(path, 'w') as f:
            json.dump(self, f, indent=4, cls=spec_encoder)

class spec_encoder(json.JSONEncoder):
    def default(self, obj):
        if (isinstance(obj, spec_config) or isinstance(obj, spec_run) or isinstance(obj, props) or isinstance(obj,                                                                                             propitem)):
            return obj.tojson()
        return super(spec_encoder, self).default(obj)


class spec_decoder(json.JSONDecoder):
    def __init__(self, *args, **kwargs):
        json.JSONDecoder.__init__(self, object_hook=self.object_hook, *args, **kwargs)

    def object_hook(self, obj):
        type = obj.get('_type', '')
        if type == 'spec_config':
            return spec_config(obj)
        templates = obj.get('TemplateData', '')
        if (templates != ''):
            return self.decode_tate(obj, templates)
        return obj

    def decode_tate(self, obj, templates):
        runlist = obj.get('RunList', '')
        if (runlist == ''):
            raise AssertionError("Json file has no run lists")
        #Run lists is a list, templates is a dict.
        ret = spec_config()
        ret.type = "tate_config"
        for run in runlist:
            r = spec_run()
            template_type = run.get('template_type', '')
            if(template_type == ''):
                raise AssertionError("Run in RunList has no template type")
            temp = templates.get(template_type, '')
            if(temp == ''):
                raise AssertionError("Template '{}' does not exist in TemplateData".format(temp))
            translations = temp.get('translations', {})
            for k, v in run.items():
                if k in known_args:
                    r.set_known_arg(k, v)
                    continue
                t = translations.get(k, '')
                if(t != ''):
                    r.set_by_translation(t, v)
            ret.runs.append(r)
        return ret



class spec_run:
    def __init__(self, fromjson=None):
        if (fromjson is None):
            self.properties = props()
            self.jdk = "/usr/bin/java"
            self.jvm_options = "-Xms29g -Xmx29g -Xmn27g -XX:ParallelGCThreads=48"
            self.data_collection = "NONE"
            self.num_runs = 1
            self.numa_nodes = 1
            self.tag = "tag-name"
            self.run_type = 'composite'  # must be 'multi, 'distributed_ctrl_txl', 'distributed_sut', 'multi'
            self.verbose = False
            self.report_level = 0  # must be between 0-3
            self.skip_report = False
            self.ignore_kit_validation = False
        else:
            self.jdk = fromjson.get('jdk', "/usr/bin/java")
            self.jvm_options = fromjson.get('jvm_options', "-Xms29g -Xmx29g -Xmn27g -XX:ParallelGCThreads=48")
            self.data_collection = fromjson.get('data_collection',  "NONE")
            self.num_runs = fromjson.get('num_runs', 1)
            self.tag = fromjson.get('tag', "tag-name")
            self.run_type = fromjson.get('run_type', 'composite')
            self.properties = props(fromjson.get('props', {"modified" : []}))
            self.verbose = fromjson.get('verbose', False)
            self.numa_nodes = fromjson.get('numa_nodes', 1)
            self.report_level = fromjson.get('report_level', 0)
            self.skip_report = fromjson.get('skip_report', False)
            self.ignore_kit_validation = fromjson.get('ignore_kit_validation', False)

    def set_runtype(self, arg):
        """Ensure that arg is a valid runtype before setting the runtype"""
        if (arg in run_types):
            self.run_type = arg


    def set_known_arg(self, key, value):
        if(key == 'JDK'):
            self.jdk = value
        elif key == 'JVM Options': self.jvm_options = value
        elif key == 'Run Type': self.run_type = value
        elif key == 'Tag': self.tag = value
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

    def set_by_translation(self, trans, value):
        self.properties.set(trans, value)


    def tojson(self):
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
            "props": self.properties.tojson()
        }

    def totateconfig(self):
        return {
            "template_type" : "CURSES",
            "JDK" : self.jdk,
            "JVM Options" : self.jvm_options,
            "Run Type" : self.run_type,
            "Tag" : self.tag,
            "Numa Nodes" : self.numa_nodes,
            "Verbose" : self.verbose,
            "Report Level" : self.report_level,
            "Skip Report" : self.skip_report,
            "Ignore Kit Validation" : self.ignore_kit_validation,
            "Number of Runs" : self.num_runs,
            "Data Collection" : self.data_collection,
            "props_extra" : self.properties.totateconfig()
        }

    def _defHandle(msg):
        print(msg)

    # handle = Any function that takes a single string argument.
    # It can be used to intercept any output
    # If set to None, then output will only be logged
    def run(self, path="", handle_out=_defHandle, handle_err=_defHandle):
        """
        Runs with the current settings.  Auto detects runtype, writes the config file, and executes all required processes
        :param path: The path to a directory containing 'specjbb2015.jar'
        :param handle: An output handler.  Will receive byte encoded strings?
                    If left blank, all output will be 'printed'
        :return: 0 -> All runs completed successfully
                 2 -> Failed to located 'specjbb2015.jar' in the path
                 4 -> Failed to ping the host controller
                -1 -> An error ocurred executing specjbb
        """
        if (not os.path.exists(self.jdk)):
            return 2
        if (path == ""):
            path = os.getcwd()
        if (not os.path.exists(os.path.join(path, "specjbb2015.jar"))):
            handle_err('Failed to locate "specjbb2015.jar" in "{}"'.format(path))
            return 2
        #       orig = os.getcwd()
        #        os.chdir(path)
        switch = {
            'composite': self.run_composite,
            'distributed_ctrl_txl': self.run_distributed_ctrl_txl,
            'distributed_sut': self.distributed_sut,
            'multi': self.run_multi
        }
        ret = switch[self.run_type](path, handle_out, handle_err)
        #      os.chdir(orig)
        return ret

    def run_composite(self, path, handle_out, handle_err):
        """Called internally only by this.run()"""
        cmd = '{} {} -jar {}/specjbb2015.jar -m COMPOSITE {}'.format(
            self.jdk, self.jvm_options, path, self._spec_opts())
        for x in range(self.num_runs):
            result_dir = self._prerun(path)
            handle_out('Starting run number {}.'.format(x))
            handle_out('Using command: "{}"'.format(cmd))
            errout = open(os.path.join(result_dir, 'composite.out'), 'wb')
            stdout = open(os.path.join(result_dir, 'composite.log'), 'wb')
            p = Popen(shlex.split(cmd), cwd=path, stdout=PIPE, stderr=PIPE)
            while (p.poll() is None):
                e = p.stderr.readline()
                if (e != ''):
                    errout.write(e)
                    handle_err(e)
                o = p.stdout.readline()
                if (o != ''):
                    stdout.write(o)
                    handle_out(o)
            errout.close()
            stdout.close()
            exitcode = p.wait()
            if (exitcode != 0):
                return -1

        return 0

    def run_distributed_ctrl_txl(self, path, handle_out, handle_err):
        """Called internally only by this.run()"""
        ctrl_ip = self.properties.root['specjbb.controller.host'].value

        # Check if ip responds here
        pingcmd = 'ping -c 1 {}'.format(ctrl_ip)
        FNULL = open(os.devnull, 'w')
        ping = Popen(shlex.split(pingcmd), stderr=FNULL, stdout=FNULL)
        exitcode = ping.wait()
        FNULL.close()
        if (exitcode != 0):
            handle_err('ERROR: Failed to ping Controller host (specjbb.controller.host): {}'.format(ctrl_ip))
            return 4

        opts = self._spec_opts()
        tx_opts = self._tx_opts()
        result_dir = self._prerun(path)
        cmd = '{} {} -jar {}/specjbb2015.jar -m DISTCONTROLLER {}'.format(self.jdk, self.jvm_options, path, opts)
        tx_procs = []
        cont_std = open(os.path.join(result_dir, 'controller.log'), 'wb')
        cont_err = open(os.path.join(result_dir, 'controller.out'), 'wb')
        controller = Popen(shlex.split(cmd), cwd=path, stdout=PIPE, stderr=PIPE)
        # os.system('{} {} -jar {}/specjbb2015.jar -m DISTCONTROLLER {} 2> {}/controller.log > {}/controller.out &'.format(self.jdk, self.jvm_options, path, opts, result_dir, result_dir))
        for g in range(self.properties.root['specjbb.group.count'].value):
            for j in range(self.properties.root['specjbb.txi.pergroup.count'].value):
                ti_name = "{}Group{}.TxInjector.txiJVM{}".format(result_dir, g, j)
                cmd = '{} {} -jar {}/specjbb2015.jar -m TXINJECTOR -G={}'.format(self.jdk, self.jvm_options, path,
                                                                                 tx_opts, g)
                tx_procs.append([Popen(shlex.split(cmd), cwd=path, stdout=PIPE, stderr=PIPE),
                                 open(os.path.join(result_dir, '{}.log'.format(ti_name)), 'wb'),
                                 open(os.path.join(result_dir, '{}.out'.format(ti_name)), 'wb')])
                # os.system('{} {} -jar {}/specjbb2015.jar -m TXINJECTOR -G={} 2> {}.log > {}.out &'.format(self.jdk, self.jvm_options, path, tx_opts, g, ti_name, ti_name))
        while (controller.poll() is None):
            e = controller.stderr.readline()
            if (e != ''):
                cont_err.write(e)
                handle_err(e)
            o = controller.stdout.readline()
            if (o != ''):
                cont_std.write(o)
                handle_out(o)
            for p in tx_procs:
                if (p[0].poll() is None):
                    e = p[0].stderr.readline()
                    if (e != ''):
                        p[2].write(e)
                        handle_err(e)
                    o = p[0].stdout.readline()
                    if (o != ''):
                        p[1].write(o)
                        handle_out(o)
        cont_err.close()
        cont_std.close()
        exitcode = controller.wait()
        for p in tx_procs:
            p[0].kill()
            p[1].close()
            p[2].close()
        if (exitcode != 0):
            return -1
        return 0

    def distributed_sut(self, path, handle_out, handle_err):
        """Called internally only by this.run()"""
        ctrl_ip = self.properties.root['specjbb.controller.host'].value
        # Check if ip responds here
        pingcmd = 'ping -c 1 {}'.format(ctrl_ip)
        FNULL = open(os.devnull, 'wb')
        ping = Popen(shlex.split(pingcmd), stderr=FNULL, stdout=FNULL)
        exitcode = ping.wait()
        FNULL.close()
        if (exitcode != 0):
            handle_err('ERROR: Failed to ping Controller host (specjbb.controller.host): {}'.format(ctrl_ip))
            return 4
        opts = self._tx_opts()
        procs = []
        for g in range(self.properties.root['specjbb.group.count'].value):
            be_name = 'beJVM Group{}.Backend.beJVM.log'.format(g)
            cmd = '{} {} -jar {}/specjbb2015.jar -m BACKEND {} -G={} -J=beJVM'.format(self.jdk, self.jvm_options, path,
                                                                                      opts, g)
            procs.append([Popen(shlex.split(cmd), cwd=path, stdout=PIPE, stderr=STDOUT),
                          open(os.path.join(path, be_name), 'wb')])
            # os.system('java {} -jar {}/specjbb2015.jar -m BACKEND {} -G={} -J=beJVM Group{}.Backend.beJVM.log 2>&1 &'.format(self.jdk, self.jvm_options, path, opts, g, g, g))

        dead = False
        while not dead:
            dead = True
            for p in procs:
                if (p[0].poll() is None):
                    dead = False
                    o = p[0].stdout.readline()
                    if (o != ''):
                        handle_out(o)
                        p[1].write(o)
        for p in procs:
            p[0].wait()
            p[1].close()

        # Each process will continue until manually terminated.
        return 0

    def run_multi(self, path, handle_out, handle_err):
        """Called internally only by this.run()"""
        result_dir = self._prerun(path)
        opts = self._spec_opts()
        tx_opts = self._tx_opts()
        has_numa = self._check_numa() and self.numa_nodes > 1
        numa_cmd = 'numactl --cpunodebind={} --localalloc'
        for x in range(self.num_runs):
            cont_std = open(os.path.join(result_dir, 'controller.log'), 'wb')
            cont_err = open(os.path.join(result_dir, 'controller.out'), 'wb')
            cmd = '{} {} -jar {}/specjbb2015.jar -m MULTICONTROLLER {}'.format(self.jdk, self.jvm_options, path, opts)
            controller = Popen(shlex.split(cmd), cwd=path, stdout=PIPE, stderr=PIPE)
            tx_procs = []
            be_procs = []
            # os.system('{} {} -jar {}/specjbb2015.jar -m MULTICONTROLLER {} 2> {}/controller.log > {}/controller.out &'.format(self.jdk, self.jvm_options, path, opts, x, result_dir, result_dir))
            for g in range(self.properties.root['specjbb.group.count'].value):
                numa = numa_cmd.format((g - 1) % 4)
                for j in range(self.properties.root['specjbb.txi.pergroup.count'].value):
                    ti_name = "{}Group{}.TxInjector.txiJVM{}".format(result_dir, g, j)
                    if(has_numa):
                        cmd = '{} {} {} -jar {}/specjbb2015.jar -m TXINJECTOR {} -G={}'.format(numa, self.jdk, self.jvm_options,
                                                                                            path, tx_opts, g, ti_name,
                                                                                            ti_name)
                    else:
                        cmd = '{} {} -jar {}/specjbb2015.jar -m TXINJECTOR {} -G={}'.format(self.jdk, self.jvm_options,
                                                                                        path, tx_opts, g, ti_name,
                                                                                        ti_name)
                    tx_procs.append([Popen(shlex.split(cmd), cwd=path, stdout=PIPE, stderr=PIPE),
                                     open(os.path.join(path, '{}.log'.format(ti_name)), 'wb'),
                                     open(os.path.join(path, '{}.out'.format(ti_name)), 'wb')])
                    # os.system('{} {} -jar {}/specjbb2015.jar -m TXINJECTOR {} -G={} 2> {}.log > {}.out &'.format(self.jdk, self.jvm_options, path, tx_opts, g, ti_name, ti_name))
                be_name = "{}{}.Backend.beJVM".format(result_dir, g)
                if(has_numa):
                    cmd = '{} {} {} -jar {}/specjbb2015.jar -m BACKEND {} -G={} -J=beJVM'.format(numa, self.jdk,
                                                                                              self.jvm_options,
                                                                                              path, tx_opts,
                                                                                              g)
                else:
                    cmd = '{} {} -jar {}/specjbb2015.jar -m BACKEND {} -G={} -J=beJVM'.format(self.jdk, self.jvm_options,
                                                                                          path, tx_opts,
                                                                                          g)
                be_procs.append([Popen(shlex.split(cmd), cwd=path, stdout=PIPE, stderr=PIPE),
                                 open(os.path.join(path, '{}.log'.format(be_name)), 'wb'),
                                 open(os.path.join(path, '{}.out'.format(be_name)), 'wb')])

            while (controller.poll() is None):
                e = controller.stderr.readline()
                if (e != ''):
                    cont_err.write(e)
                    handle_err(e)
                o = controller.stdout.readline()
                if (o != ''):
                    cont_std.write(o)
                    handle_out(o)
                for p in tx_procs:
                    if (p[0].poll() is None):
                        e = p[0].stderr.readline()
                        if (e != ''):
                            p[2].write(e)
                            handle_err(e)
                        o = p[0].stdout.readline()
                        if (o != ''):
                            p[1].write(o)
                            handle_out(o)
                for p in be_procs:
                    if (p[0].poll() is None):
                        e = p[0].stderr.readline()
                        if (e != ''):
                            p[2].write(e)
                            handle_err(e)
                        o = p[0].stdout.readline()
                        if (o != ''):
                            p[1].write(o)
                            handle_out(o)
            cont_err.close()
            cont_std.close()
            exitcode = controller.wait()
            for p in tx_procs:
                p[0].kill()
                p[1].close()
                p[2].close()
            for p in be_procs:
                p[0].kill()
                p[1].close()
                p[2].close()
            if (exitcode != 0):
                return -1
            # os.system(
            #    '{} {} -jar {}/specjbb2015.jar -m BACKEND {} -G={} -J=beJVM 2> {}.log > {}.out &'.format(self.jdk,
            #                                                                                              self.jvm_options,
            ##                                                                                             path, tx_opts,
            #                                                                                             g, be_name,
            #                                                                                             be_name))

        return 0

    def _prerun(self, path):
        """Called internally only.  Builds a result directory and writes the current config to it."""
        result_dir = "{}/{}-{}".format(path, datetime.datetime.fromtimestamp(time.time()).strftime('+%y-%m-%d_%H%M%S'),
                                       self.tag)
        os.makedirs(result_dir)
        if (not os.path.exists("{}/config".format(path))):
            os.makedirs("{}/config".format(path))
        self.properties.writeconfig("{}/config/specjbb2015.props".format(path))
        return result_dir

    def _tx_opts(self):
        """Called internally only.  Obtains specjbb options available to TXINJECTOR and BACKEND"""
        opts = ""
        if (self.verbose):
            opts += " -v"
        if (self.ignore_kit_validation):
            opts += " -ikv"
        return opts

    def _spec_opts(self):
        """Called internally only.  Obtains specjbb options available to all except TXINJECTOR and BACKEND"""
        opts = "-l {}".format(self.report_level)
        if (self.skip_report):
            opts += " -skipReport"
        if (self.verbose):
            opts += " -v"
        if (self.ignore_kit_validation):
            opts += " -ikv"
        return opts

    def _check_numa(self):
        p = Popen(shlex.split('which numactl'), stdout=PIPE)
        o, e = p.communicate()
        result = len(o) > 0
        p.wait()
        return result


class propitem:
    def __init__(self, prop, def_value, desc, input_validator, value_validator, valid_opts=None, help_text=""):
        self.prop = prop
        self.def_value = def_value
        self.desc = desc
        self.input_validator = input_validator
        self.value_validator = value_validator
        self.help_text = help_text
        if (valid_opts is None):
            self.valid_opts = []
        else:
            self.valid_opts = valid_opts
        self.value = def_value

    def write(self, f):
        """Called internally only.  Writes to a config file if different than the default value"""
        if (self.value != self.def_value):
            f.write("{} = {}".format(self.prop, self.value))

    def set(self, arg):
        """Use this to set this property value using a validator"""
        if (self.value_validator(arg)):
            self.value = arg

    def reset(self):
        """Resets this property to the default value"""
        self.value = self.def_value

    def totateconfig(self):return self.tojson()

    def tojson(self):
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

number_validator = lambda x: int(x) <= ord('9') and int(x) >= ord('0')
float_validator = lambda x: (x <= ord('9') and x >= ord('0')) or x == ord('.')
default_validator = lambda x: True

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
             'Sets duration of settle period of RT step level in milliseconds', number_validator, lambda x: int(x) > 0,
             help_text=must_be_positive),
    propitem('specjbb.controller.settle.time.max', 30000,
             'Sets duration of settle period of RT step level in milliseconds', number_validator, lambda x: int(x) > 0,
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

    propitem('specjbb.logLevel', 'INFO', 'Log level output', default_validator, lambda x: x in loglevels, loglevels),

    propitem('specjbb.time.check.interval', 10000,
             'Time interval (in milliseconds) for periodic time check from Time Server', number_validator,
             lambda x: int(x) > 0, help_text=must_be_positive),
    propitem('specjbb.time.offset.max', 600000,
             'Maximum time offset (in milliseconds) between Controller and Time Server on the benchmark start',
             number_validator, lambda x: int(x) > 0, help_text=must_be_positive)
]


class props:
    def __init__(self, fromjson=None):
        self.root = {a.prop: a for a in defaults}
        if (not fromjson is None):
            for p in fromjson.get('modified', []):
                self.root.update({p['prop']: p['value']})

    def set(self, key, value):
        """Can be used to set a specific property to a value using a validator"""
        if (key in self.root and self.root[key].value_validator(value)):
            self.root[key].value = value

    def get_all(self):
        """Returns a list of 'propitem's"""
        return list(self.root.values())

    def get_modified(self):
        """Returns a list of modified 'propitem's"""
        return [x for x in list(self.root.values()) if isinstance(x, propitem) and x.value != x.def_value]

    def writeconfig(self, path):
        """Called internally only before running any 'spec_run'"""
        with open(path, 'w') as f:
            f.write("#SPECjbb config")
            for p in self.root.values():
                if (isinstance(p, propitem)):
                    p.write(f)

    def tojson(self):
        """Called internally only.  Returns dictionary of json values"""
        return {
            "modified": list(map(lambda x: x.tojson(), self.get_modified()))
        }

    def totateconfig(self):
        return {
            "props_extra" : list(map(lambda x: x.tojson(), self.get_modified()))
        }
