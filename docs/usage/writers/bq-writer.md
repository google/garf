!!! important
    To save data to BigQuery install `garf-io` with BigQuery support

    ```bash
    pip install garf-io[bq]
    ```


`bq` writer allows you to save `GarfReport` to BigQuery table.

/// tab | cli
```bash
garf query.sql --source API_SOURCE \
  --output bq
```
///

/// tab | python
```python
from garf.core import report
from garf.io.writers import bigquery_writer

# Create example report
sample_report = report.GarfReport(results=[[1]], column_names=['one'])

writer = bigquery_writer.BigQueryWriter()
writer.write(sample_report, 'query')
```
///

## Parameters
### project

By default reports are saved to `GOOGLE_CLOUD_PROJECT`.
You can overwrite it with `project` parameter.

/// tab | cli
```bash hl_lines="3"
garf query.sql --source API_SOURCE \
  --output bq \
  --bq.project=PROJECT_ID
```
///

/// tab | python
```python hl_lines="7"
from garf.core import report
from garf.io.writers import bigquery_writer

# Create example report
sample_report = report.GarfReport(results=[[1]], column_names=['one'])

writer = bigquery_writer.BigQueryWriter(project="PROJECT_ID")
writer.write(sample_report, 'query')
```
///

### dataset

By default reports are saved to `garf` dataset.
You can overwrite it with `dataset` parameter.

/// tab | cli
```bash hl_lines="3"
garf query.sql --source API_SOURCE \
  --output bq \
  --bq.dataset=DATASET
```
///

/// tab | python
```python hl_lines="7"
from garf.core import report
from garf.io.writers import bigquery_writer

# Create example report
sample_report = report.GarfReport(results=[[1]], column_names=['one'])

writer = bigquery_writer.BigQueryWriter(dataset="DATASET")
writer.write(sample_report, 'query')
```
///

### location

By default reports are saved to `US` location.
You can overwrite it with `location` parameter.

/// tab | cli
```bash hl_lines="3"
garf query.sql --source API_SOURCE \
  --output bq \
  --bq.location=LOCATION
```
///

/// tab | python
```python hl_lines="7"
from garf.core import report
from garf.io.writers import bigquery_writer

# Create example report
sample_report = report.GarfReport(results=[[1]], column_names=['one'])

writer = bigquery_writer.BigQueryWriter(location="LOCATION")
writer.write(sample_report, 'query')
```
///

### write_disposition

By default reports overwrite any existing data.
You can overwrite it with [`write_disposition`](https://cloud.google.com/bigquery/docs/reference/auditlogs/rest/Shared.Types/BigQueryAuditMetadata.WriteDisposition) parameter.

/// tab | cli
```bash hl_lines="3"
garf query.sql --source API_SOURCE \
  --output bq \
  --bq.write_disposition=WRITE_APPEND
```
///

/// tab | python
```python hl_lines="7"
from garf.core import report
from garf.io.writers import bigquery_writer

# Create example report
sample_report = report.GarfReport(results=[[1]], column_names=['one'])

writer = bigquery_writer.BigQueryWriter(write_disposition="WRITE_APPEND")
writer.write(sample_report, 'query')
```
///

### time_partitioning_column

By default all reports are written into a single table. With `time_partitioning_column`
you can [partition your table](https://docs.cloud.google.com/bigquery/docs/partitioned-tables)
by HOUR, DAY, MONTH or YEAR.

/// tab | cli
```bash hl_lines="3"
garf query.sql --source API_SOURCE \
  --output bq \
  --bq.time_partitioning_column=COLUMN
```
///

/// tab | python
```python hl_lines="7"
from garf.core import report
from garf.io.writers import bigquery_writer

# Create example report
sample_report = report.GarfReport(results=[[1]], column_names=['one'])

writer = bigquery_writer.BigQueryWriter(time_partitioning_column="COLUMN")
writer.write(sample_report, 'query')
```
///

### time_partitioning_type

Type of time partitioning (`DAY`, `HOUR`, `MONTH`, `YEAR`).

/// tab | cli
```bash hl_lines="3"
garf query.sql --source API_SOURCE \
  --output bq \
  --bq.time_partitioning_type=DAY
```
///

/// tab | python
```python hl_lines="7"
from garf.core import report
from garf.io.writers import bigquery_writer

# Create example report
sample_report = report.GarfReport(results=[[1]], column_names=['one'])

writer = bigquery_writer.BigQueryWriter(time_partitioning_type="DAY")
writer.write(sample_report, 'query')
```
///

### time_partitioning_expiration_ms

Expiration of time partitioned tables in milliseconds.

/// tab | cli
```bash hl_lines="3"
garf query.sql --source API_SOURCE \
  --output bq \
  --bq.time_partitioning_expiration_ms=2592000000
```
///

/// tab | python
```python hl_lines="7"
from garf.core import report
from garf.io.writers import bigquery_writer

# Create example report
sample_report = report.GarfReport(results=[[1]], column_names=['one'])

writer = bigquery_writer.BigQueryWriter(time_partitioning_expiration_ms=2592000000)
writer.write(sample_report, 'query')
```
///

### range_partitioning_column

Column to [partition tables into ranges](https://docs.cloud.google.com/bigquery/docs/partitioned-tables#integer_range).

/// tab | cli
```bash hl_lines="3"
garf query.sql --source API_SOURCE \
  --output bq \
  --bq.range_partitioning_column=COLUMN
```
///

/// tab | python
```python hl_lines="7"
from garf.core import report
from garf.io.writers import bigquery_writer

# Create example report
sample_report = report.GarfReport(results=[[1]], column_names=['one'])

writer = bigquery_writer.BigQueryWriter(range_partitioning_column="COLUMN")
writer.write(sample_report, 'query')
```
///

### range_partitioning_range

Range definition in `start:end:interval` format.

/// tab | cli
```bash hl_lines="3"
garf query.sql --source API_SOURCE \
  --output bq \
  --bq.range_partitioning_range=0:1000:10
```
///

/// tab | python
```python hl_lines="7"
from garf.core import report
from garf.io.writers import bigquery_writer

# Create example report
sample_report = report.GarfReport(results=[[1]], column_names=['one'])

writer = bigquery_writer.BigQueryWriter(range_partitioning_range="0:1000:10")
writer.write(sample_report, 'query')
```
///

### clustering_columns

Column(s) to perform [clustering of table](https://docs.cloud.google.com/bigquery/docs/clustered-tables).
Can be provided as a comma-separated string.

/// tab | cli
```bash hl_lines="3"
garf query.sql --source API_SOURCE \
  --output bq \
  --bq.clustering_columns=col1,col2
```
///

/// tab | python
```python hl_lines="7"
from garf.core import report
from garf.io.writers import bigquery_writer

# Create example report
sample_report = report.GarfReport(results=[[1]], column_names=['one'])

writer = bigquery_writer.BigQueryWriter(clustering_columns="col1,col2")
writer.write(sample_report, 'query')
```
///
