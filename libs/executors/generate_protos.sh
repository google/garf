python -m grpc_tools.protoc -I=../../protos/ \
	--python_out=./garf/executors --grpc_python_out=./garf/executors \
	../../protos/garf.proto
