# garf Helm charts

Helm chart to install garf server into Kubernetes.


## Components

* `garf` - garf HTTP server.
* `garf-worker` - celery worker to handle query / workflows executions.
* `redis` - optional Redis instance to facility communication between server and worker(s).

## Install

```bash
helm repo add garf https://google.github.io/garf/
helm repo update
helm install garf garf/garf -n garf --create-namespace
```

## Customization

You can customize Helm chart by overwriting default values:

* `garf.server.type` - choose between http or grpc (http is default one).
* `garf.worker.enabled` - whether to enable celery worker (enabled by default).
* `garf.otel.enabled` - whether to sending data to OpenTelemetry collector (disabled by default).

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

If you enable garf worker, you might want to override some default redis values.

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

To explore the full values that can be customized dump them to `values.yaml`:


```bash
helm show values garf/garf > values.yaml
```

Once you set necessary configuration options, you can apply them:

```bash
helm upgrade garf garf/garf -n garf -f values.yaml
```

## Uninstall

```bash
helm uninstall garf -n garf
```
