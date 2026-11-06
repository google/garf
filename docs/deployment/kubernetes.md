`garf` can run in Kubernetes as a long-running [exporter](#expose-metrics-for-prometheus),
and can schedule executions of [queries](../usage/executors.md) and
[workflows](../usage/workflows.md) as jobs or cronjobs.

There are two ways to deploy `garf` to Kubernetes:

1. [Helm chart](#install-into-kubernetes-via-helm) - install garf server (and workers) into your cluster.
2. [garf operator](#run-garf-jobs-and-cronjobs-via-operator) - simplified execution of garf jobs & cronjobs.

## Install into Kubernetes via Helm

The Helm chart installs several components:

* `garf` - garf HTTP server.
* `garf-worker` - celery worker to handle query / workflows executions.
* `redis` - optional Redis instance to facilitate communication between server and worker(s).

### Prerequisites

Helm added to your local environment:

```bash
helm repo add garf https://google.github.io/garf/
helm repo update
```

### Deploy

This will deploy `garf` as a HTTP or gRPC server which you can call indendently.

```bash
helm install garf garf/garf -n garf --create-namespace
```

### Prepare configuration

You can customize the Helm chart by overwriting the default values:

* `garf.server.type` - choose between http or grpc (http is default one).
* `garf.worker.enabled` - whether to enable celery worker (enabled by default).
* `garf.otel.enabled` - whether to send data to OpenTelemetry collector (disabled by default).

```yaml
garf:
  server:
    type: http
    replicaCount: 1
  worker:
    enabled: true
    replicaCount: 1
  otel:
    enabled: false
    serviceName: garf
    otelExporterOtlpEndpoint: ""
```

If you enable garf worker, you might want to override some default Redis values:

```yaml
redis:
  enabled: true

  auth:
    enabled: true
    password: "redisadmin123"
  architecture: "standalone"
  master:
    persistence:
      enabled: true
      size: "1Gi"
```

!!!note
    To explore the full set of customizable values dump them to `values.yaml`:

    ```bash
    helm show values garf/garf > values.yaml
    ```

### Apply changes

Once you set necessary configuration options, you can apply them:

```bash
helm upgrade garf garf/garf -n garf -f values.yaml
```

### Uninstall

```bash
helm uninstall garf -n garf
```

## Run garf jobs and cronjobs via operator

`garf operator` allows you to run [queries](../usage/executors.md)
and [workflows](../usage/workflows.md) as jobs and cronjobs, as well as set up instances of
[garf exporter](../usage/exporters.md) to expose metrics for Prometheus.

### Prerequisites

1. `garf` gRPC server installed in your Kubernetes cluster - you can use the
   [Helm chart](#install-into-kubernetes-via-helm) with `garf.server.type: grpc`.
2. `kubectl` configured against your cluster.

### Deploy operator and custom resources

Apply garf custom resource definitions:

```bash
kubectl apply -f https://raw.githubusercontent.com/google/garf/refs/heads/main/kubernetes-operator/garf-crd.yaml
```

Then deploy the operator:

```bash
kubectl apply -f https://raw.githubusercontent.com/google/garf/refs/heads/main/kubernetes-operator/garf-operator.yaml
```

### Create jobs and cronjobs

`garf-operator` supports two types of (cron)jobs - Workflow and Query.

!!!important
    If schedule is omitted then the object is treated as Job.

#### Workflow

Workflow (and its corresponding [config](../usage/configs.md)) can be provided as a file path
(usually a file stored in a remote storage - GCS, S3, HTTP, etc.) or mapped via ConfigMap.

1. Workflow path

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

#### Queries

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

## Expose metrics for Prometheus

`garf exporter` exposes garf-extracted data in Prometheus format and is created via custom
resources provisioned by the operator.

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

!!!note
    By default each pod created by the exporter is annotated so it is found by Prometheus
    service discovery:

    ```
    'prometheus.io/path': '/metrics'
    'prometheus.io/port': '8000'
    'prometheus.io/scrape': 'true'
    ```
