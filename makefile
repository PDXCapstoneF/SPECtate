test:
	python -m unittest discover
proto:
	python -m grpc_tools.protoc \
		-Isrc \
		--python_out=. \
		--grpc_python_out=. \
		spectate.proto
clean:
	rm -rf src/proto src/*_pb2.py
