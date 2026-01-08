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
from garf_core import report
from garf_io.writers import bigquery_writer

# Create example report
sample_report = report.GarfReport(results=[[1]], column_names=['one'])

writer = bigquery_writer.BigQueryWriter()
writer.write(sample_report, 'query')
```
///

## Parameters
### Project

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
from garf_core import report
from garf_io.writers import bigquery_writer

# Create example report
sample_report = report.GarfReport(results=[[1]], column_names=['one'])

writer = bigquery_writer.BigQueryWriter(project="PROJECT_ID")
writer.write(sample_report, 'query')
```
///

### Dataset

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
from garf_core import report
from garf_io.writers import bigquery_writer

# Create example report
sample_report = report.GarfReport(results=[[1]], column_names=['one'])

writer = bigquery_writer.BigQueryWriter(dataset="DATASET")
writer.write(sample_report, 'query')
```
///

### Location

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
from garf_core import report
from garf_io.writers import bigquery_writer

# Create example report
sample_report = report.GarfReport(results=[[1]], column_names=['one'])

writer = bigquery_writer.BigQueryWriter(location="LOCATION")
writer.write(sample_report, 'query')
```
///

### Write disposition

By default reports overwrite any existing data.
You can overwrite it with [`write_disposition`](https://cloud.google.com/bigquery/docs/reference/auditlogs/rest/Shared.Types/BigQueryAuditMetadata.WriteDisposition) parameter.

/// tab | cli
```bash hl_lines="3"
garf query.sql --source API_SOURCE \
  --output bq \
  --bq.write_disposition=DISPOSITION
```
///

/// tab | python
```python hl_lines="7"
from garf_core import report
from garf_io.writers import bigquery_writer

# Create example report
sample_report = report.GarfReport(results=[[1]], column_names=['one'])

writer = bigquery_writer.BigQueryWriter(write_disposition="DISPOSITION")
writer.write(sample_report, 'query')
```
///
