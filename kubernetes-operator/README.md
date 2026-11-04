# garf operator - simplified garf jobs & cronjobs execution in Kubernetes


garf operator allows you to run [queries](https://google.github.io/garf/usage/executors/)
and [workflows](https://google.github.io/garf/usage/workflows/) as jobs and cronjobs
as well as setup instances of [garf exporter](https://google.github.io/garf/usage/exporters/)
to expose metrics for Prometheus.

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

`garf-operator` supports two types of (cron)jobs - Workflow and Query.

If schedule is omitted that the object is treated as Job.


### Workflows

Workflow (and their corresponding [config](https://google.github.io/garf/usage/configs/) can be provided as a file path
(usually a file stored in some remote storage - GCS, S3, HTTP, etc.)
or mapped via ConfigMap.

1. Workflow Path

```yaml
apiVersion: garf.io/v1
kind: Workflow
metadata:
  name: garf-workflow
spec:
  schedule: "*/30 * * * *"
  workflowPath: path/to/workflow.yaml
  configPath: path/to/config.yaml
  server:
    url: <server_address:port>
    server_type: <SERVER_TYPE>
  env: []
```

2. Workflow ConfigMap

```yaml
apiVersion: garf.io/v1
kind: Workflow
metadata:
  name: garf-workflow
spec:
  schedule: "*/30 * * * *"
  configMaps:
    workflow:
      name: garf-workflows
      key: my-workflow.yaml
    config:
      name: garf-configs
      key: my-config.yaml
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

## Create exporters

garf exporter allows you expose garf-extracted data in Prometheus format.


```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: collectors
data:
  fake.yaml: |-
    - title: test
      query: |
        SELECT
          dimension.string AS field,
          metrics.int AS clicks
        FROM fake
        LIMIT 10
---
apiVersion: garf.io/v1
kind: Exporter
metadata:
  name: garf-fake-exporter
spec:
  source: fake
  configMaps:
    - name: collectors
      key: fake.yaml
  env: []
```

By default each pod created by this exporter has  the following annotation
to ensure that it is found by Prometheus service discovery.

```json
'prometheus.io/path': '/metrics',
'prometheus.io/port': '8000',
'prometheus.io/scrape': 'true'
```
