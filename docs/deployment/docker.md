# Docker

## Run as a HTTP Service


1. Start service on port 8000

```bash
docker run -p 8000:8000 ghcr.io/google/garf:latest
```

2. Call it

```bash
curl -X 'POST' \
  'http://0.0.0.0:8000/api/execute' \
  -H 'accept: application/json' \
  -H 'Content-Type: application/json' \
  -d '{
  "source": "rest",
  "title": "test",
  "query": "SELECT id AS device_id, name AS device_name, data.color AS device_color FROM objects",
  "context": {
    "fetcher_parameters": {
      "endpoint": "https://api.restful-api.dev"
    }
  }
}'
```

## Run as a gRPC Service


1. Start service on port  50051

```bash
docker run -p 50051:50051 ghcr.io/google/garf:latest \
  python -m garf.executors.entrypoints.grpc_server
```



## Run as a CLI tool

```bash
docker run ghcr.io/google/garf:latest \
  'SELECT id AS device_id, name AS device_name, data.color AS device_color FROM objects' \
  --input console --output console --source rest \
  --rest.endpoint=https://api.restful-api.dev \
  --logger rich
```
