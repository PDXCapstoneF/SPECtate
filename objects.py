import json
import multiprocessing
import os
import time

import datetime




class spec_config():
    #runs contains a list of spec_run's
    def __init__(self, fromjson = None):
        self.runs = []
        if(not fromjson is None):
            for r in fromjson['runs']:
                self.runs.append(spec_run(r))

    def tojson(self):
        return {
            "_type" : "spec_config",
            "runs" : map(lambda x:x.tojson(), self.runs)
        }

    def save(self, path):
        with open(path, 'w') as f:
            json.dump(self, f, cls=spec_encoder)



class spec_encoder(json.JSONEncoder):
    def default(self, obj):
        if(isinstance(obj, spec_config) or isinstance(obj, spec_run) or isinstance(obj, props) or isinstance(obj, propitem)):
            return obj.tojson()
        return super(spec_encoder, self).default(obj)

class spec_decoder(json.JSONDecoder):
    def __init__(self, *args, **kwargs):
        json.JSONDecoder.__init__(self, object_hook=self.object_hook, *args, **kwargs)

    def object_hook(self, obj):
        if '_type' not in obj:
            return obj
        type = obj['_type']
        if type == 'spec_config':
            return spec_config(obj)
        return obj


run_types = [
    'composite',
    'distributed_ctrl_txl',
    'distributed_sut',
    'multi'
]

class spec_run:
    def __init__(self, fromjson = None):
        if(fromjson is None):
            self.properties = props()
            self.jdk = "jdk.8-u121"
            self.jvm_options = "-Xms29g -Xmx29g -Xmn27g -XX:ParallelGCThreads=48"
            self.data_collection = "NONE"
            self.num_runs = 1
            self.numa_nodes = 1
            self.tag = "tag-name"
            self.run_type = 'composite'
        else:
            self.jdk = fromjson['jdk'],
            self.jvm_options = fromjson['jvm_options']
            self.data_collection = fromjson['data_collection']
            self.num_runs = fromjson['num_runs']
            self.tag = fromjson['tag']
            self.run_type = fromjson['run_type']
            self.properties = props(fromjson['props'])

    def set_runtype(self, arg):
        if(arg in run_types):
            self.run_type = arg

    def runtype(self):
        return self.run_type

    def tojson(self):
        return {
            "jdk" : self.jdk,
            "jvm_options" : self.jvm_options,
            "data_collection" : self.data_collection,
            "num_runs" : self.num_runs,
            "run_type" : self.run_type,
            "tag" : self.tag,
            "props" :  self.properties.tojson()
        }


    def run(self, path = ""):
        if(path == ""):
            path = os.getcwd()
        if(not os.path.exists(os.path.join(path, "specjbb2015.jar"))):
            return 2
 #       orig = os.getcwd()
#        os.chdir(path)
        switch = {
            'composite': self.run_composite,
            'distributed_ctrl_txl' : self.run_distributed_ctrl_txl,
            'distributed_sut' : self.distributed_sut,
            'multi' : self.run_multi
        }
        ret = switch[self.run_type](path)
  #      os.chdir(orig)
        return ret


    def run_composite(self, path):
        for x in range(self.num_runs):
            result_dir = self._prerun(path)
 #           spec = os.subprocess.Popen(['/usr/bin/java' "{}/specjbb2015.jar".format(path)])
            os.system('java {} -jar {}/specjbb2015.jar -m COMPOSITE 2> {}/composite.log > {}/composite.out &'.format(self.jvm_options, path, result_dir, result_dir))
        return 0

    def run_distributed_ctrl_txl(self, path):
        ctrl_ip = self.properties.root['specjbb.controller.host'].value
        #Check if ip responds here
        result_dir= self._prerun(path)
        os.system('java {} -jar {}/specjbb2015.jar -m DISTCONTROLLER 2> {}/controller.log > {}/controller.out &'.format(self.jvm_options, path, result_dir, result_dir))
        for g in range(self.properties.root['specjbb.group.count'].value):
            for j in range(self.properties.root['specjbb.txi.pergroup.count'].value):
                ti_name = "{}Group{}.TxInjector.txiJVM{}".format(result_dir, g, j)
                os.system('java {} -jar {}/specjbb2015.jar -m TXINJECTOR -G={} 2> {}.log > {}.out &'.format(self.jvm_options, path, g, ti_name, ti_name))
        return 0

    def distributed_sut(self, path):
        ctrl_ip = self.properties.root['specjbb.controller.host'].value
        #Check if ip responds here
        for g in range(self.properties.root['specjbb.group.count'].value):
            os.system('java {} -jar {}/specjbb2015.jar -m BACKEND -G={} -J=beJVM Group{}.Backend.beJVM.log 2>&1 &'.format(self.jvm_options, path, g, g, g))

        return 0

    def run_multi(self, path):

        for x in range(self.num_runs):
            result_dir= self._prerun(path)
            os.system('java {} -jar {}/specjbb2015.jar -m MULTICONTROLLER 2> {}/controller.log > {}/controller.out &'.format(self.jvm_options, path, x, result_dir, result_dir))
            for g in range(self.properties.root['specjbb.group.count'].value):
                for j in range(self.properties.root['specjbb.txi.pergroup.count'].value):
                    ti_name = "{}Group{}.TxInjector.txiJVM{}".format(result_dir, g, j)
                    os.system('java {} -jar {}/specjbb2015.jar -m TXINJECTOR -G={} 2> {}.log > {}.out &'.format(self.jvm_options, path, g, ti_name, ti_name))

        be_name = "{}{}.Backend.beJVM".format(result_dir, g)
        os.system('java {} -jar {}/specjbb2015.jar -m BACKEND -G={} -J=beJVM 2> {}.log > {}.out &'.format(self.jvm_options, path, x, be_name, be_name))
        return 0

    def _prerun(self, path):
        result_dir = "{}/{}".format(path, datetime.datetime.fromtimestamp(time.time()).strftime('+%y-%m-%d_%H%M%S'))
        os.makedirs(result_dir)
        if (not os.path.exists("{}/config".format(path))):
            os.makedirs("{}/config".format(path))
        self.properties.writeconfig("{}/config/specjbb2015.props".format(path))
        return result_dir




class propitem:
    def __init__(self, prop, def_value, desc, validator, t='int', valid_opts = None):
        self.prop = prop
        self.def_value = def_value
        self.desc = desc
        self.validator = validator
        self.type = t
        if(valid_opts is None):
            self.valid_opts = []
        else:
            self.valid_opts = valid_opts
        self.value = def_value

    def write(self, f):
        if(self.value != self.def_value):
            f.write("{} = {}".format(self.prop, self.value))

    def set(self, arg):
        if(self.validator(arg)):
            self.value = arg

    def reset(self):
        self.value = self.def_value

    def convert(self, str):
        if(self.type == 'int'):
            return strtoint(str)
        if (self.type == 'str'):
            return str
        if (self.type == 'float'):
            return strtofloat(str)
        if (self.type == 'bool'):
            return strtobool(str)

    def tojson(self):
        return {
   #         "_type" : "propitem",
            "prop" : self.prop,
            "value" : self.value
        }




loglevels = [
    'SEVERE',
    'WARNING',
    'INFO',
    'CONFIG',
    'FINE',
    'FINER',
    'FINEST'
]

def strtobool(str):
    if str.lower() in ("yes", "true", "t", "1"):
        return True
    if str.lower() in ("no", "false", "f", "0"):
        return False
    return None

def strtoint(str):
    try:
        return int(str)
    except:
        return None

def strtofloat(str):
    try:
        return float(str)
    except:
        return None

con_types = [
    'HBIR_RT',
    'HBIR',
    'PRESET',
    'FIXED_RT',
    'FIXED_RT_LOADLEVELS',
    'FIXED_LOADLEVELS'
]

defaults = [
propitem('specjbb.controller.type', 'HBIR_RT', 'Controls phases being controlled by Controller.', lambda x: isinstance(x, str) and x in con_types, 'str', con_types),
  propitem('specjbb.comm.connect.client.pool.size', 256, 'Network connection pool size, i.e. number of sockets for I/O communication for each Agent.', lambda x:isinstance(x, int),'int',[]),
propitem('specjbb.comm.connect.worker.pool.min', 1,'Minimum number of worker threads in the network connection pool.', lambda x:isinstance(x, int),'int',[]),
propitem('specjbb.comm.connect.worker.pool.max', 256, 'Maximum number of worker threads in the network connection pool.',lambda x:isinstance(x, int),'int',[]),
propitem('specjbb.comm.connect.selector.runner.count', 0,'Number of acceptor threads for handling new connections and scheduling existing ones.', lambda x:isinstance(x, int),'int',[]),
    propitem('specjbb.comm.connect.timeouts.connect', 60000,'Timeout (in milliseconds) for I/O connection operation.', lambda x:isinstance(x, int),'int',[]),
    propitem('specjbb.comm.connect.timeouts.read' ,60000, 'Timeout (in milliseconds) for I/O read operation.', lambda x:isinstance(x, int),'int',[]),
   propitem('specjbb.comm.connect.timeouts.write' ,  60000, 'Timeout (in milliseconds) for I/O write operation.',lambda x:isinstance(x, int),'int',[]),

propitem('specjbb.controller.host', "localhost", 'IP address / host name of the machine where Controller program will be launched.', lambda x:isinstance(x, str),'str',[]),
propitem('specjbb.controller.port', 24000, 'The network port to which Controller listener will bind.', lambda x:isinstance(x, int),'int',[]),

    propitem('specjbb.controller.handshake.period',5000, 'Time period (in milliseconds) for logging status of the initial Controller <-> Agent handshaking.', lambda x:isinstance(x, int),'int',[]),
    propitem('specjbb.controller.handshake.timeout' ,600000, 'Timeout (in milliseconds) for initial Controller <-> Agent handshaking.', lambda x:isinstance(x, int),'int',[]),
    propitem('specjbb.controller.maxir.maxFailedPoints',3, ' Number of points to try after max-jOPS was found to ensure there are no more passes and max-jOPS value is correct.', lambda x: isinstance(x, int),'int',[]),

propitem('specjbb.controller.preset.ir', 1000, 'Sets IR for preset for controller type ',lambda x: isinstance(x, int),'int',[]),
propitem('specjbb.controller.preset.duration', 600000, 'Sets duration in milliseconds for preset for controller type ',lambda x: isinstance(x, int),'int',[]),

propitem('specjbb.controller.rtcurve.duration.min', 60000, 'Sets duration of steady period of RT step level in milliseconds', lambda x: isinstance(x, int),'int',[]),
propitem('specjbb.controller.rtcurve.duration.max', 90000, 'Sets duration of steady period of RT step level in milliseconds',lambda x: isinstance(x, int),'int',[]),
propitem('specjbb.controller.rtcurve.start', 0.0, 'Sets the RT start percent', lambda x: isinstance(x, float),'float',[]),
propitem('specjbb.controller.rtcurve.step', 0.01,'Sets the RT step level to a percent', lambda x: isinstance(x, float),'float',[]),
propitem('specjbb.controller.rtcurve.warmup.step', 0.1, 'Injection rate for warming up before response-time curve building defined as the percent of the high-bound.', lambda x: isinstance(x, float),'float',[]),

propitem('specjbb.controller.settle.time.min', 3000,'Sets duration of settle period of RT step level in milliseconds', lambda x: isinstance(x, int) ,'int',[]),
propitem('specjbb.controller.settle.time.max', 30000, 'Sets duration of settle period of RT step level in milliseconds',lambda x: isinstance(x, int),'int',[]),




#propitem('specjbb.customerDriver.threads', 64, 'Maximum number of threads in ThreadPoolExecutor for all three probe/saturate/service requests on the TxInjector side.', lambda x: isinstance(x, int) and x >= 64,[])
propitem('specjbb.customerDriver.threads.saturate', 64,  'Maximum number of threads in ThreadPoolExecutor for saturate requests on the TxInjector side.', lambda x: isinstance(x, int),'int',[]),
propitem('specjbb.customerDriver.threads.probe', 64,  'Maximum number of threads in ThreadPoolExecutor for probe requests on the TxInjector side.', lambda x: isinstance(x, int),'int',[]),
propitem('specjbb.customerDriver.threads.service', 64,  'Maximum number of threads in ThreadPoolExecutor for service requests on the TxInjector side.', lambda x: isinstance(x, int),'int',[]),
#propitem('specjbb.forkjoin.workers', multiprocessing.cpu_count() * 2, 'Maximum number of worker threads in ForkJoinPool in each tier on the Backend side.', lambda x:isinstance(x, int),[])
    propitem('specjbb.forkjoin.workers.Tier1', multiprocessing.cpu_count() * 2, 'Maximum number of worker threads in ForkJoinPool in tier 1 on the Backend side.', lambda x:isinstance(x, int),'int',[]),
    propitem('specjbb.forkjoin.workers.Tier2', multiprocessing.cpu_count() * 2, 'Maximum number of worker threads in ForkJoinPool in tier 2 on the Backend side.', lambda x:isinstance(x, int),'int',[]),
    propitem('specjbb.forkjoin.workers.Tier3', multiprocessing.cpu_count() * 2, 'Maximum number of worker threads in ForkJoinPool in tier 3 on the Backend side.', lambda x:isinstance(x, int),'int',[]),
propitem('specjbb.group.count', 1, 'Number of Groups for the run, where Group is TxInjector(s) mapped to Backend.', lambda x:isinstance(x, int) and x > 0,'int',[]),

  propitem('specjbb.heartbeat.period', 10000, 'How often (in milliseconds) Controller sends heartbeat message to an Agent checking it is alive',lambda x: isinstance(x, int),'int',[]),
propitem('specjbb.heartbeat.threshold', 100000,  'How much time (in milliseconds) await for heartbeat response from an Agent.',lambda x: isinstance(x, int),'int',[]),

propitem('specjbb.time.server', False, 'Enables Controller communication with Time Server.', lambda x:isinstance(x, bool),'bool',['False', 'True']),
   propitem('specjbb.txi.pergroup.count', 1, 'Number of TxInjectors per Backend in one Group.', lambda x: isinstance(x, int) and x > 0,'int',[]),

propitem('specjbb.run.datafile.dir', '.', 'Directory for storing binary log file of the run.', lambda x:isinstance(x, int),'int',[]),
propitem('specjbb.mapreducer.pool.size', 2, 'Controller ForkJoinPool size supporting parallel work of TxInjector/Backend agents.', lambda x:isinstance(x, int),'int',[]),

propitem('specjbb.input.number_customers', 100000, 'Total number of customers', lambda x:isinstance(x, int),'int',[]),
propitem('specjbb.input.number_products', 100000, ' Number of products in each Supermarket', lambda x:isinstance(x, int),'int',[]),

propitem('specjbb.logLevel', 'INFO' , 'Log level output', lambda x:isinstance(x, str) and x in loglevels, 'str',loglevels),

propitem('specjbb.time.check.interval', 10000, 'Time interval (in milliseconds) for periodic time check from Time Server', lambda x:isinstance(x, int) and x >=0,'int',[]),
propitem('specjbb.time.offset.max', 600000, 'Maximum time offset (in milliseconds) between Controller and Time Server on the benchmark start',lambda x:isinstance(x, int) and x >=0,'int',[])
]

hbir = [
    'specjbb.controller.rtcurve.start',
    'specjbb.group.count',
    'specjbb.forkjoin.workers.Tier1',
    'specjbb.forkjoin.workers.Tier2',
    'specjbb.forkjoin.workers.Tier3',
]
loadlevels = [
    'specjbb.controller.loadlevel.duration.min',
    'specjbb.controller.loadlevel.duration.max',
    'specjbb.controller.rtcurve.start',
    'specjbb.group.count',
    'specjbb.forkjoin.workers.Tier1',
    'specjbb.forkjoin.workers.Tier2',
    'specjbb.forkjoin.workers.Tier3',
]
presets =[
    'specjbb.controller.preset.ir',
    'specjbb.controller.preset.duration',
    'specjbb.group.count',
    'specjbb.forkjoin.workers.Tier1',
    'specjbb.forkjoin.workers.Tier2',
    'specjbb.forkjoin.workers.Tier3',
]
defhbir = [
('specjbb.time.server',False),
('specjbb.comm.connect.client.pool.size', 192),
('specjbb.comm.connect.selector.runner.count', 4),
('specjbb.comm.connect.timeouts.connect', 650000),
('specjbb.comm.connect.timeouts.read', 650000),
('specjbb.comm.connect.timeouts.write', 650000),
('specjbb.comm.connect.worker.pool.max', 320),
('specjbb.customerDriver.threads', 64),
('specjbb.customerDriver.threads.saturate', 144),
('specjbb.customerDriver.threads.probe', 96),
('specjbb.mapreducer.pool.size', 27),
]
defloadlevels = [
('specjbb.controller.loadlevel.start ',  .95),
('specjbb.controller.loadlevel.step ',  1),
('specjbb.time.server', False),

('specjbb.comm.connect.client.pool.size', 192),
('specjbb.comm.connect.selector.runner.count', 4),
('specjbb.comm.connect.timeouts.connect', 650000),
('specjbb.comm.connect.timeouts.read', 650000),
('specjbb.comm.connect.timeouts.write', 650000),
('specjbb.comm.connect.worker.pool.max', 320),
('specjbb.customerDriver.threads', 64),
('specjbb.customerDriver.threads.saturate', 144),
('specjbb.customerDriver.threads.probe', 96),
('specjbb.mapreducer.pool.size', 27),
]
defpresets =[
('specjbb.comm.connect.client.pool.size', 192),
('specjbb.comm.connect.selector.runner.count', 4),
('specjbb.comm.connect.timeouts.connect', 650000),
('specjbb.comm.connect.timeouts.read', 650000),
('specjbb.comm.connect.timeouts.write', 650000),
('specjbb.comm.connect.worker.pool.max', 320),
('specjbb.customerDriver.threads', 64),
('specjbb.customerDriver.threads.saturate', 144),
('specjbb.customerDriver.threads.probe', 96),
('specjbb.mapreducer.pool.size', 27)
]

def get_important(type):
    return {
        'HBIR_RT':1,
        'HBIR':1,
        'PRESET':1,
        'FIXED_RT':1,
        'FIXED_RT_LOADLEVELS':1,
        'FIXED_LOADLEVELS':1
    }.get(type)

class props:
    def __init__(self, fromjson = None):
        self.root ={a.prop : a for a in defaults}
        #dict(zip(lambda x:{x.prop: x}, defaults))
        if(not fromjson is None):
            for p in fromjson['modified']:
                self.root.update({p['prop'], p['value']})

    def set(self, key, value):
        if(key in self.root and self.root[key].validator(value)):
            self.root[key].value = value

    def get_all(self):
        return self.root.values()

    def get_modified(self):
        return [x for x in self.root.values() if x.value != x.def_value]

    def writeconfig(self, path):
        with open(path, 'w') as f:
            f.write("#SPECjbb config")
            for p in self.root.values():
                p.write(f)
            #f.writelines(map(lambda x:"{}={}".format(x.prop, x.value), filter(lambda x:x.value != x.def_value, self.dict.itervalues())))

    def tojson(self):
        return {
            "modified" : map(lambda x:x.tojson(), self.get_modified())
        }
