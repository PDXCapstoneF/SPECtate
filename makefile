test:
	python -m unittest discover
proto:
	python -m grpc_tools.protoc \
		-Isrc \
		--python_out=src/proto \
		--grpc_python_out=src/proto \
		src/spectate.proto
clean:
	rm -rf src/proto
