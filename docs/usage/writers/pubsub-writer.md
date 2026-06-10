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
### project

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

sample_report = report.GarfReport(results=[[1]], column_names=['one'])

writer = pubsub_writer.PubSubWriter(project="ANOTHER_PROJECT_ID")
writer.write(sample_report, 'topic_name')
```
///

### push_strategy

By default PubSub writer pushes the whole report in a body.
You can overwrite it with `push_strategy` parameter which supports three options:

  * `report` - pushes the whole report as a message.
  * `batch` - pushes N rows of report into a message.
  * `row` - pushes each row of report into a separate message.

/// tab | cli
```bash hl_lines="3"
garf query.sql --source API_SOURCE \
  --output pubsub \
  --pubsub.push-strategy=row
```
///

/// tab | python
```python hl_lines="7"
from garf.core import report
from garf.io.writers import pubsub_writer

sample_report = report.GarfReport(results=[[1]], column_names=['one'])

writer = pubsub_writer.PubSubWriter(push_strategy='row')
writer.write(sample_report, 'topic_name')
```
///

### batch_size

For `batch` `push_strategy` the default number of messages in a batch is `10`.
You can overwrite it with `batch_size` parameter.

/// tab | cli
```bash hl_lines="3"
garf query.sql --source API_SOURCE \
  --output pubsub \
  --pubsub.push-strategy=batch \
  --pubsub.batch-size=5
```
///

/// tab | python
```python hl_lines="7"
from garf.core import report
from garf.io.writers import pubsub_writer

sample_report = report.GarfReport(results=[[1]], column_names=['one'])

writer = pubsub_writer.PubSubWriter(push_strategy='batch', batch_size=5)
writer.write(sample_report, 'topic_name')
```
///
