!!! important
    To save data to Kafka install `garf-io` with Kafka support

    ```bash
    pip install garf-io[kafka]
    ```


`kafka` writer allows you to publish `GarfReport` to a Kafka topic.

/// tab | cli
```bash
garf query.sql --source API_SOURCE \
  --output kafka \
  --kafka.bootstrap_servers=localhost:9092
```
///

/// tab | python
```python
from garf.core import report
from garf.io.writers import kafka_writer

# Create example report
sample_report = report.GarfReport(results=[[1]], column_names=['one'])

writer = kafka_writer.KafkaWriter(bootstrap_servers='localhost:9092')
writer.write(sample_report, 'topic_name')
```
///

## Parameters
### Bootstrap Servers

By default it connects to `localhost:9092`.
You can overwrite it with `bootstrap_servers` parameter.

/// tab | cli
```bash hl_lines="3"
garf query.sql --source API_SOURCE \
  --output kafka \
  --kafka.bootstrap_servers=broker1:9092,broker2:9092
```
///

/// tab | python
```python hl_lines="7"
from garf.core import report
from garf.io.writers import kafka_writer

# Create example report
sample_report = report.GarfReport(results=[[1]], column_names=['one'])

writer = kafka_writer.KafkaWriter(bootstrap_servers="broker1:9092,broker2:9092")
writer.write(sample_report, 'topic_name')
```
///

### push_strategy

By default Kafka writer pushes the whole report in a body.
You can overwrite it with `push_strategy` parameter which supports three options:

  * `report` - pushes the whole report as a message.
  * `batch` - pushes N rows of report into a message.
  * `row` - pushes each row of report into a separate message.

/// tab | cli
```bash hl_lines="3"
garf query.sql --source API_SOURCE \
  --output kafka \
  --kafka.push-strategy=row
```
///

/// tab | python
```python hl_lines="7"
from garf.core import report
from garf.io.writers import kafka_writer

sample_report = report.GarfReport(results=[[1]], column_names=['one'])

writer = kafka_writer.KafkaWriter(push_strategy='row')
writer.write(sample_report, 'topic_name')
```
///

### batch_size

For `batch` `push_strategy` the default number of messages in a batch is `10`.
You can overwrite it with `batch_size` parameter.

/// tab | cli
```bash hl_lines="3"
garf query.sql --source API_SOURCE \
  --output kafka \
  --kafka.push-strategy=batch \
  --kafka.batch-size=5
```
///

/// tab | python
```python hl_lines="7"
from garf.core import report
from garf.io.writers import kafka_writer

sample_report = report.GarfReport(results=[[1]], column_names=['one'])

writer = kafka_writer.KafkaWriter(push_strategy='batch', batch_size=5)
writer.write(sample_report, 'topic_name')
```
///
