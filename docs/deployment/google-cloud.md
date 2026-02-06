
## Cloud Run

0. Prerequisites

```bash
gcloud projects add-iam-policy-binding $GOOGLE_CLOUD_PROJECT \
    --member="serviceAccount:$(gcloud projects describe $GOOGLE_CLOUD_PROJECT \
    --format='value(projectNumber)')@cloudbuild.gserviceaccount.com" \
    --role="roles/run.admin"

gcloud projects add-iam-policy-binding $GOOGLE_CLOUD_PROJECT \
    --member="serviceAccount:$(gcloud projects describe $GOOGLE_CLOUD_PROJECT \
    --format='value(projectNumber)')@cloudbuild.gserviceaccount.com" \
    --role="roles/iam.serviceAccountUser"
```

1. Prepare `cloudbuild.yaml`


```yaml
steps:
  - name: 'gcr.io/cloud-builders/docker'
    args: [
      'build',
      '-t', 'gcr.io/$PROJECT_ID/garf:latest',
      '--build-arg', 'EXTRA_LIBS=${_EXTRA_LIBS}',
      '.'
    ]

  - name: 'gcr.io/cloud-builders/docker'
    args: ['push', 'gcr.io/$PROJECT_ID/garf:latest']

  - name: 'gcr.io/google.com/cloudsdktool/cloud-sdk'
    entrypoint: gcloud
    args: [
      'run', 'deploy', 'garf',
      '--image', 'gcr.io/$PROJECT_ID/garf:latest',
      '--region', 'us-central1',
      '--platform', 'managed', '--port', '8000',
      '--set-env-vars',
      'OTEL_EXPORTER_OTLP_ENDPOINT=telemetry.googleapis.com,OTEL_SERVICE_NAME=garf',
    ]

substitutions:
  _EXTRA_LIBS: "garf-executors"

images:
  - 'gcr.io/$PROJECT_ID/garf:latest'
```

2. Deploy Cloud run with optional libraries

```bash
gcloud builds submit --config cloudbuild.yaml \
  --substitutions=_EXTRA_LIBS="garf-youtube garf-google-ads garf-executors[bq]"
```

## Cloud Workflows

If you want to call `garf`, use Cloud Workflows.


1. Define workflow by populating assignment `pairs`

```yaml
main:
  params: [args]
  steps:
    - init:
        assign:
          - pairs:
            - alias: ALIAS
              source: FETCHER
              queries:
                - query:
                    title: 'title'
                    text: |
                      SELECT
                       ...
              fetcher_parameters:
                param1: value
                param2: ${args.value}
              writer: WRITER_TYPE
              writer_parameters:
                param1: ${sys.get_env("GARF_PARAM")}
                param2: value
              context:
                query_parameters:
                  macro:
                    start_date: ':YYYYMMDD-10'
                    end_date: ':YYYYMMDD-1'
                  template: {}
                  ...
    - run:
        for:
          value: pair
          in: ${pairs}
          steps:
            - log_source:
                call: sys.log
                args:
                  data: ${pair.alias}
            - execute_queries:
                parallel:
                  for:
                    value: query
                    in: ${pair.queries}
                    steps:
                      - log_query:
                          call: sys.log
                          args:
                            data: ${pair}
                      - execute_single_query:
                          try:
                            call: http.post
                            args:
                              url: ${sys.get_env("GARF_ENDPOINT") + "/api/execute"}
                              auth:
                                type: OIDC
                              body:
                                source: ${pair.source}
                                title: ${query.query.title}
                                query: ${query.query.text}
                                context:
                                  fetcher_parameters: ${pair.fetcher_parameters}
                                  writer: ${pair.writer}
                                  writer_parameters: ${pair.writer_parameters}
                                  query_parameters:
                                    macro: ${pair.context.query_parameters.macro}
                                    template: ${pair.context.query_parameters.template}
                            result: task_resp
                          except:
                            as: e
                            assign:
                              - task_resp:
                                  status: "failed"
                                  error: ${e.message}
                      - log_result:
                          call: sys.log
                          args:
                            data: ${task_resp}
```


2. Deploy

```bash
gcloud workflows deploy WORKFLOW_NAME --source=WORKFLOW_FILE.yaml \
  --set-env-vars GARF_ENDPOINT=VALUE1,GARF_PARAM=PARAM1
```

3. Run

```bash
gcloud workflows run WORKFLOW_NAME \
  --data='{
  "arg1":"arg1_value",
  "arg2":"arg2_value"
}'
```
