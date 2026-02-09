!!! important
    To save data to Google Cloud Pub/Sub install `garf-io` with PubSub support

    ```bash
    pip install garf-io[pubsub]
    ```


`pubsub` writer allows you to publish `GarfReport` to a Google Cloud Pub/Sub topic.

/// tab | cli
```bash
garf query.sql --source API_SOURCE \
  --output pubsub \
  --pubsub.project=PROJECT_ID
```
///

/// tab | python
```python
from garf.core import report
from garf.io.writers import pubsub_writer

# Create example report
sample_report = report.GarfReport(results=[[1]], column_names=['one'])

writer = pubsub_writer.PubSubWriter(project='PROJECT_ID')
writer.write(sample_report, 'topic_name')
```
///

## Parameters
### Project

By default it uses `GOOGLE_CLOUD_PROJECT` environment variable.
You can overwrite it with `project` parameter.

/// tab | cli
```bash hl_lines="3"
garf query.sql --source API_SOURCE \
  --output pubsub \
  --pubsub.project=ANOTHER_PROJECT_ID
```
///

/// tab | python
```python hl_lines="7"
from garf.core import report
from garf.io.writers import pubsub_writer

# Create example report
sample_report = report.GarfReport(results=[[1]], column_names=['one'])

writer = pubsub_writer.PubSubWriter(project="ANOTHER_PROJECT_ID")
writer.write(sample_report, 'topic_name')
```
///
