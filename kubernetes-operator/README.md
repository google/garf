# garf operator - simplified garf cronjob execution in Kubernetes

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

## Create cronjobs

`garf-operator` supports two types of cronjobs - Workflow and Queries.


### Workflows

```yaml
apiVersion: garf.io/v1
kind: GarfWorkflowCronJob
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
kind: GarfQueryCronJob
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
