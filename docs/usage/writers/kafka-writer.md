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
