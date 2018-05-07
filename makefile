test:
	python -m unittest discover
proto:
	python -m grpc_tools.protoc \
		-Isrc \
		--python_out=src \
		--grpc_python_out=src \
		src/spectate.proto
clean:
	rm -rf src/proto src/*_pb2.py
