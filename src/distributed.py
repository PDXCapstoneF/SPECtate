from concurrent import futures
import time
import logging
import json

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
        t = task_runner.TaskRunner(request.java, 
                *request.java_options, "-m", *request.component_options)
        t.run()
        return spectate_pb2.BenchmarkResults(results_path="anywhere")

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

def to_run_configuration(run):
    """
    Adapts a run that would be submit to SpecJBBRun to a
    protobuf equivalent.
    """
    log.debug("(client) recieved run configuration {}".format(run))
    
    def to_pair(p):
        return spectate_pb2.SPECjbbPair(**{
            "prop_name": p[0],
            "value": str(p[1]),
            "type": type(p[1]).__name__,
            })

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
