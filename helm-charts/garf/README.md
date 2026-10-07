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

## Uninstall

```bash
helm uninstall garf -n garf
```
