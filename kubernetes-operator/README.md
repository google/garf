# garf operator - simplified garf jobs & cronjobs execution in Kubernetes

## Prerequisites

* `garf` gRPC server installed in your Kubernetes cluster. Refer to [helm documentation](../helm-charts/garf/README.md) on installing one.

## Installation

* Apply garf custom resource definitions:

```bash
kubectl apply -f https://raw.githubusercontent.com/google/garf/refs/heads/main/kubernetes-operator/garf-crd.yaml
```

* Deploy operator and custom resources:

```bash
kubectl apply -f https://raw.githubusercontent.com/google/garf/refs/heads/main/kubernetes-operator/garf-operator.yaml
```

## Create jobs & cronjobs

`garf-operator` supports two types of jobs & cronjobs - Workflow and Query.

If schedule is omitted that the object is treated as Job.


### Workflows

```yaml
apiVersion: garf.io/v1
kind: Workflow
metadata:
  name: garf-workflow
spec:
  schedule: "*/30 * * * *"
  workflowPath: path/to/workflow.yaml
  server:
    url: <server_address:port>
    server_type: <SERVER_TYPE>
  env: []
```

### Queries

```yaml
apiVersion: garf.io/v1
kind: Queries
metadata:
  name: garf-query
spec:
  schedule: "*/30 * * * *"
  queries:
    - path: path/to/query.sql
  source: <FETCHER_ALIAS>
  writer: <WRITER_TYPE>
  context:
    fetcher_parameters: {}
    writer_parameters: {}
  server:
    url: <server_address:port>
    server_type: <SERVER_TYPE>
  env: []
```
