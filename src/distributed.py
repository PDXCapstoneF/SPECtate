from concurrent import futures
import time
import logging
import json
import configparser
from pydoc import locate

import grpc
from uuid import uuid4

import spectate_pb2
import spectate_pb2_grpc

from src import benchmark_run
from src import task_runner
from src import run_generator # TODO: remove

log = logging.getLogger(__name__)

class SPECtateDistributedRunnerServicer(spectate_pb2_grpc.SPECtateDistributedRunnerServicer):
    def DoBenchmarkRun(self, request, context):
        log.debug("(server) recieved request")

        props = dict()

        # coerce prop types
        for p in request.props:
            t = locate(p.type)
            props[p.prop_name] = t(p.value)

        # write props file
        def do_component():
            benchmark_run.write_props_to_file(request.props_file, props)

            # run the given task
            t = task_runner.TaskRunner(request.java, "-jar", request.jar,
                    *request.java_options, *request.spec_options,
                    "-p", request.props_file)

            # run it in a results directory and return the path
            t.run()


        path = benchmark_run.run_in_result_directory(do_component, uuid4().hex)

        return spectate_pb2.BenchmarkResults(results_path=path)

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

def to_run_configuration(meta, run):
    """
    Adapts a run that would be submit to SpecJBBRun to a
    protobuf equivalent.
    """
    log.debug("(client) recieved run configuration")
    
    proto_props = map(to_pair, meta.props.items())
    log.info("run configured {}".format(run))
    spec_options = ["-m", run["type"].upper()] + run.options + ["-G", run["-G"], "-J", run["-J"]]
    return spectate_pb2.RunConfiguration(
            java=meta.java.path,
            jar=meta.jar,
            java_options=meta.java.options,
            spec_options=spec_options,
            props_file=meta.props_file,
            props=proto_props,
        )


def submit_run(meta, component):
    """Submits a run to a listening SPECtate server."""
    channel = grpc.insecure_channel(component["host"])
    stub = spectate_pb2_grpc.SPECtateDistributedRunnerStub(channel)
    response = stub.DoBenchmarkRun(to_run_configuration(meta, component))
    log.info("SPECtate client received: {}".format(response))

def test(filename):
    with open(filename, 'r') as f:
        l = f.read()
    example = json.loads(l)
    rg = run_generator.RunGenerator(**example)
    
    for run in rg.runs:
        s = benchmark_run.SpecJBBRun(**run)
        for component in s.components_grouped():
            log.debug("component: {}".format(component))
            submit_run(s, component)
