from concurrent import futures
import time
import logging
import json
import configparser
from pydoc import locate

import grpc

import spectate_pb2
import spectate_pb2_grpc

from src import benchmark_run
from src import task_runner
from src import run_generator # TODO: remove

log = logging.getLogger(__name__)

class SPECtateDistributedRunnerServicer(spectate_pb2_grpc.SPECtateDistributedRunnerServicer):
    def DoBenchmarkRun(self, request, context):
        log.debug("(server) recieved request: {}".format(request))
        props = dict()
        props_file_location = 'specjbb2015.props'

        # coerce prop types
        for p in request.props:
            t = locate(p.type)
            props[p.prop_name] = t(p.value)

        # write props file
        with open(props_file_location, 'w+') as props_file:
            c = configparser.ConfigParser()
            c.read_dict({'SPECtate': props})
            c.write(props_file)

        # run the given task
        t = task_runner.TaskRunner(request.java, 
                *request.java_options, "-p", props_file_location, 
                *request.component_options)

        return spectate_pb2.BenchmarkResults(results_path=t.run())

def listen():
    """Starts a server listening for SPECtate actions."""
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    spectate_pb2_grpc.add_SPECtateDistributedRunnerServicer_to_server(SPECtateDistributedRunnerServicer(), server)
    server.add_insecure_port('[::]:50051')
    server.start()
    try:
        while True:
            time.sleep(60 * 24 * 24)
    except KeyboardInterrupt:
        server.stop(0)

def to_pair(p):
    name, value = p
    return spectate_pb2.SPECjbbPair(**{
        "prop_name": name,
        "value": str(value),
        "type": type(value).__name__,
        })

def to_run_configuration(run):
    """
    Adapts a run that would be submit to SpecJBBRun to a
    protobuf equivalent.
    """
    log.debug("(client) recieved run configuration {}".format(run))
    
    props = map(to_pair, run["props"].items())

    return spectate_pb2.RunConfiguration(
        java=run["java"],
        java_options=["-jar", run["jar"]],
        component=spectate_pb2.BACKEND, # TODO: how do we split these out
        component_options=[],
        props=props,
        )


def submit_run(run):
    """Submits a run to a listening SPECtate server."""
    channel = grpc.insecure_channel('localhost:50051')
    stub = spectate_pb2_grpc.SPECtateDistributedRunnerStub(channel)
    response = stub.DoBenchmarkRun(to_run_configuration(run))
    print("SPECtate client received: {}".format(response))

def test():
    with open('example_config.json', 'r') as f:
        l = f.read()
    example = json.loads(l)
    rg = run_generator.RunGenerator(**example)
    
    for run in rg.runs:
        submit_run(run)
