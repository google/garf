python -m grpc_tools.protoc -I=../../protos/ \
	--python_out=./garf_executors --grpc_python_out=./garf_executors \
	../../protos/garf.proto
