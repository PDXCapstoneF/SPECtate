import grpc
import spectate_pb2
import spectate_pb2_grpc

class SPECtateDistributedRunnerServicer(spectate_pb2_grpc.SPECtateDistributedRunnerServicer):
    def DoBenchmarkRun(self, request, context):
        return spectate_pb2.BenchmarkResults(results_path="anywhere")

def listen():
    channel = grpc.insecure_channel('localhost:80')
    stub = spectate_pb2_grpc.SPECtateDistributedRunnerStub(channel)

    # listen for a distributed run request
    response = stub.DoBenchmarkRun(spectate_pb2.RunConfiguration(**{
        "java": "java",
        "component": spectate_pb2.BACKEND,
        }))

    print("SPECtate client received: " + response)
