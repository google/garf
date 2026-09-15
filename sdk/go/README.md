# Go SDK for garf server

## Prerequisites

* `garf` gRPC server running; expose as `GARF_ENDPOINT` variable.

## Run

### Execute query

```bash
GARF_ENDPOINT=127.0.0.1:50051 go run . \
  execute examples/execute_query/query.sql \
  --source fake --writer json
```

### Execute workflow

```bash
GARF_ENDPOINT=127.0.0.1:50051 go run . \
  workflow run examples/execute_workflow/test_workflow.yaml
```

## Examples

[examples](examples/) folder contains several examples of using garf Go SDK
in your projects:

* Run query from text and file
* Run workflow
* Run batch of queries
* Fetching data and returning data back to go
* Calling helper functions (i.e. get available fetchers)
