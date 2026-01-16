# Kubernetes


## Deployment and service

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: garf
  labels:
    app: garf
spec:
  replicas: 1
  selector:
    matchLabels:
      app: garf
  template:
    metadata:
      labels:
        app: garf
    spec:
      containers:
       name: garf
        image: ghcr.io/google/garf:latest
        ports:
        - containerPort: 8000

---
apiVersion: v1
kind: Service
metadata:
  name: garf
spec:
  selector:
      app: garf
  type: NodePort
  ports:
    - protocol: TCP
      port: 30003
      targetPort: 8000
```


## Cron job


```yaml

apiVersion: batch/v1
kind: CronJob
metadata:
  name: garf-rest
spec:
  schedule: "0 * * * *"
  jobTemplate:
    spec:
      template:
        spec:
          containers:
            - name: garf
              image: ghcr.io/google/garf:latest
              imagePullPolicy: IfNotPresent
              command: ["garf"]
              args:
                - "'SELECT id AS device_id, name AS device_name, data.color AS device_color FROM objects'"
                - "--input"
                - "console"
                - "--source"
                - "rest"
                - "--source.endpoint=https://api.restful-api.dev"
                - "--output"
                - "csv"
                - "--logger"
                - "local"
          restartPolicy: OnFailure
```
