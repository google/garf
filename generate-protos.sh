python() {
	python -m grpc_tools.protoc -I=protos/ \
		--python_out=./libs/executors/garf/executors \
		--grpc_python_out=./libs/executors/garf/executors \
		protos/garf.proto
}
go() {
	protoc --proto_path=protos/ \
	--go_out=sdk/go/garf/ --go_opt=paths=source_relative \
    --go-grpc_out=sdk/go/garf/ --go-grpc_opt=paths=source_relative \
		protos/garf.proto
}
python
