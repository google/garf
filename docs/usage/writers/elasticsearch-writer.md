!!! important
    To save data to Elasticsearch install `garf-io` with Elasticsearch support

    ```bash
    pip install garf-io[elasticsearch]
    ```


`elasticsearch` writer allows you to index `GarfReport` to Elasticsearch.

/// tab | cli
```bash
garf query.sql --source API_SOURCE \
  --output elasticsearch \
  --elasticsearch.hosts=localhost:9200
```
///

/// tab | python
```python
from garf.core import report
from garf.io.writers import elasticsearch_writer

# Create example report
sample_report = report.GarfReport(results=[[1]], column_names=['one'])

writer = elasticsearch_writer.ElasticsearchWriter(hosts='localhost:9200')
writer.write(sample_report, 'index_name')
```
///

## Parameters
### Hosts

By default it connects to `localhost:9200`.
You can overwrite it with `hosts` parameter.

/// tab | cli
```bash hl_lines="3"
garf query.sql --source API_SOURCE \
  --output elasticsearch \
  --elasticsearch.hosts=host1:9200,host2:9200
```
///

/// tab | python
```python hl_lines="7"
from garf.core import report
from garf.io.writers import elasticsearch_writer

# Create example report
sample_report = report.GarfReport(results=[[1]], column_names=['one'])

writer = elasticsearch_writer.ElasticsearchWriter(hosts=["host1:9200", "host2:9200"])
writer.write(sample_report, 'index_name')
```
///

### Authentication

You can provide authentication credentials using `http_auth` parameter (Python only).

/// tab | python
```python hl_lines="7"
from garf.core import report
from garf.io.writers import elasticsearch_writer

# Create example report
sample_report = report.GarfReport(results=[[1]], column_names=['one'])

writer = elasticsearch_writer.ElasticsearchWriter(
    hosts='localhost:9200',
    http_auth=('user', 'password')
)
writer.write(sample_report, 'index_name')
```
///
