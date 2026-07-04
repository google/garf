garf() {
	python -m grpc_tools.protoc -I=protos/ \
		--python_out=./libs/executors/garf/executors \
		--grpc_python_out=./libs/executors/garf/executors \
		protos/garf.proto
}
garf
