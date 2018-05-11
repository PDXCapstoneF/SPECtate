from concurrent import futures
import os
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
from src import run_generator  # TODO: remove

log = logging.getLogger(__name__)


class SPECtateDistributedRunnerServicer(
        spectate_pb2_grpc.SPECtateDistributedRunnerServicer):

    def RunBenchmarkComponent(self, request, context):
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
            t = task_runner.TaskRunner(
                request.java, "-jar", request.jar, *request.java_options,
                *request.spec_options, "-p", request.props_file)

            t.run()

        # run it in a results directory and return the path
        path = benchmark_run.run_in_result_directory(do_component, uuid4().hex)

        return spectate_pb2.BenchmarkResults(results_path=path)


def listen(port="[::]:50051"):
    """Starts a server listening for SPECtate actions."""
    log.info("starting a SPECtate server listening on {}".format(port))
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    spectate_pb2_grpc.add_SPECtateDistributedRunnerServicer_to_server(
        SPECtateDistributedRunnerServicer(), server)
    server.add_insecure_port(port)
    server.start()
    log.info("started server successfully, awaiting requests...")
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

    proto_props = map(to_pair, meta["props"].items())
    log.info("run configured {}".format(run))
    spec_options = ["-m", run["type"].upper()
                   ] + run["options"] + ["-G", run["-G"], "-J", run["-J"]]
    return spectate_pb2.RunConfiguration(
        java=meta["java"]["path"],
        jar=meta["jar"],
        java_options=meta["java"]["options"],
        spec_options=spec_options,
        props_file=meta["props_file"],
        props=proto_props,
    )


def submit_run(meta, component):
    """Submits a run to a listening SPECtate server."""

    log.debug("component opening channel to {}".format(component["host"]))
    channel = grpc.insecure_channel(component["host"])

    log.debug("instantiating stub for SPECtateDistributedRunner")
    stub = spectate_pb2_grpc.SPECtateDistributedRunnerStub(channel)

    log.debug("running distributed benchmarking component")
    run_configuration = to_run_configuration(meta, component)
    response = stub.RunBenchmarkComponent(run_configuration)

    log.info("distributed SPECtate component received: {}".format(response))
    return response

def get_hostname(hostname_or_port):
    """
    Strips a port specification off of a hostname.
    """
    if ":" not in hostname_or_port:
        return hostname_or_port
    return ('').join(hostname_or_port.split(":")[:-1])

def collect_result(hostname, remote_path, local_path, delete=False):
    """
    Collects a directory from 
    a remote source to a local directory.
    """
    hostname = get_hostname(hostname)
    local_path = os.path.abspath(local_path)

    scp = task_runner.TaskRunner("scp", "-r", "{}:{}".format(hostname, remote_path), local_path)

    and_remove = task_runner.TaskRunner("ssh", hostname,
                            "rm -rf {}".format(remote_path))

    scp.run()

    if delete and hostname != "localhost":
        and_remove.run()

class DistributedComponent(dict):
    def __init__(self, meta, component):
        if "host" not in component:
            raise Exception("Missing host for DistributedComponent")

        self.meta = meta
        self.component = component

    def run(self):
        log.info("submitting distributed component: {}".format(self.component))
        results_path = submit_run(self.meta, self.component).results_path
        log.info("collecting result from host {}".format(self.component["host"]))
        collect_result(hostname=self.component["host"], 
                remote_path=results_path, 
                local_path=".",
                delete=True)

def test(filename):
    with open(filename, 'r') as f:
        l = f.read()
    example = json.loads(l)
    rg = run_generator.RunGenerator(**example)

    for run in rg.runs:
        s = benchmark_run.SpecJBBRun(**run)
        for component in s.components_grouped():
            log.debug("component: {}".format(component))
            if "host" in component:
                submit_run(s._meta(), component)
            else:
                log.info("skipping: {}".format(component))
