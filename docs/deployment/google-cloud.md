`garf` can be easily deployed to Google Cloud as a Cloud Run service or as a part of
Cloud Workflows.

## Cloud Run

Before using `garf` in Google Cloud we need to submit an image to Cloud Build.

### Prerequisites

Ensure that service account has necessary permissions:

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


The following command builds the image and create a Cloud Run service `garf`.

```bash
gcloud builds submit
  --config <(curl -s https://raw.githubusercontent.com/google/garf/refs/heads/main/gcp/cloudbuild.yaml) \
  --substitutions=_EXTRA_LIBS="garf-youtube garf-google-ads garf-executors[bq]" .
```

!!!note
    You can provide additional libraries via `_EXTRA_LIBS` substitutions.

    For example to interact with Google Ads API you need to install `garf-google-ads` library.


## Cloud Workflows

If you have a Cloud Run service deployed you can use it a [Cloud Workflows](https://docs.cloud.google.com/workflows/docs).

### Prerequisites

1. Workflows API enabled

    ```bash
    gcloud services enable workflows.googleapis.com
    ```

2. LogWriter role granted to default service account

    ```bash
    PROJECT_ID=$(gcloud projects describe $GOOGLE_CLOUD_PROJECT \ --format='value(projectNumber)')
    gcloud projects add-iam-policy-binding $GOOGLE_CLOUD_PROJECT \
      --member="serviceAccount:$PROJECT_ID-compute@developer.gserviceaccount.com" \
      --role=roles/logging.logWriter
    ```

### Prepare

!!!important
    You can convert your existing [workflow file](../usage/workflows.md) into
    Cloud Workflow yaml file with a helper command:

    ```bash
    grf worflow deploy -f path/to/workflow.yaml -o path/to/google-cloud-workflow.yaml
    ```

Once you have a `google-cloud-workflow.yaml` file you can deploy Cloud Workflow
based on it.


### Deploy

```bash
GARF_CLOUD_RUN_URL=$(gcloud run services describe garf --region=us-central1 --format='value(status.url)')

gcloud workflows deploy WORKFLOW_NAME \
  --source=path/to/google-cloud-workflow.yaml \
  --set-env-vars GARF_ENDPOINT=$GARF_CLOUD_RUN_URL
```


After workflow is deployed you can visit Cloud Workflow page in Google Cloud Console
and trigger or schedule it.
