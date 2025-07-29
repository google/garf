# Use garf as FastAPI endpoint

## Installation

Install `garf` with support for FastAPI endpoint

```
pip install garf-executors[server]
```

## Start

```bash
python garf_executors.entrypoints.server
```

## Query

```
curl -X 'POST' \
  'http://127.0.0.1:8000/api/execute' \
  -H 'accept: application/json' \
  -H 'Content-Type: application/json' \
  -d '{
  "source": "fake",
  "title": "example",
  "query": "SELECT campaign FROM campaign",
  "context": {
    "writer": "console",
     "writer_params": {
       "format": "json"
     }
  }
}'
```
