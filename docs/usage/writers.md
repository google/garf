# Writing GarfReport

[![PyPI](https://img.shields.io/pypi/v/garf-io?logo=pypi&logoColor=white&style=flat-square)](https://pypi.org/project/garf-io)
[![Downloads PyPI](https://img.shields.io/pypi/dw/garf-io?logo=pypi)](https://pypi.org/project/garf-io/)

`garf-io` library is reponsible for writing [`GarfReport`](reports.md) to various local/remote storages.


| CLI identifier | Writer Class           | Options  |
|------------| ---------------- | -------- |
| `console`  | ConsoleWriter    | `page-size=10`,`format=table|json|jsonl`|
| `csv`      | CsvWriter        | `destination-folder` |
| `json`     | JsonWriter       | `destination-folder`,`format=json|jsonl`|
| `bq`       | BigQueryWriter   | `project`, `dataset`, `location`, `write-disposition` |
| `sqldb`    | SqlAlchemyWriter | `connection-string`, `if-exists=fail|replace|append` |
| `sheets`   | SheetsWriter     | `share-with`, `credentials-file`, `spreadsheet-url`, `is_append=True|False`|


## Installation

/// tab | pip
```bash
pip install garf-io
```
///

/// tab | uv
```bash
uv pip install garf-io
```
///

By default  `garf-io` has only support for `console`, `csv` and `json` writers.

To install all writers use the following command `pip install garf-io[all]`.

To install specific writers use:

* `pip install garf-io[bq]` for BigQuery support
* `pip install garf-io[sheets]` for Google spreadsheets support
* `pip install garf-io[sqlalchemy]` for SqlAlchemy support


## Usage

!!!note
    To use `cli` example you need to have `garf-executors` package installed.

    ```bash
    pip install garf-executors
    ```

/// tab | cli
```bash
garf query.sql --source API_SOURCE \
  --output YOUR_WRITER
```
///

/// tab | python
```python
from garf_core import report
from garf_io import writer

# Create example report
sample_report = report.GarfReport(results=[[1]], column_names=['one'])

concrete_writer = writer.create_writer('YOUR_WRITER')
concrete_writer.write(sample_report, 'query')
```
///
!!!note
    You can use `awrite` method to write report asynchronously.
    ```python
    await concrete_writer.awrite(sample_report, 'query')
    ```

### Console

`console` writer allows you to print `GarfReport` to standard output in the terminal.

/// tab | cli
```bash
garf query.sql --source API_SOURCE \
  --output console
```
///

/// tab | python
```python
from garf_core import report
from garf_io.writers import console_writer

# Create example report
sample_report = report.GarfReport(results=[[1]], column_names=['one'])

writer = console_writer.ConsoleWriter()
writer.write(sample_report, 'query')
```
///

#### Format

For `console` writer you can specify the output format:

* `table` - rich table (default).
* `json` - JSON.
* `jsonl` - JSON lines

/// tab | cli
```bash hl_lines="3"
garf query.sql --source API_SOURCE \
  --output console \
  --console.format=json
```
///

/// tab | python
```python hl_lines="7"
from garf_core import report
from garf_io.writers import console_writer

# Create example report
sample_report = report.GarfReport(results=[[1]], column_names=['one'])

writer = console_writer.ConsoleWriter(format='json')
writer.write(sample_report, 'query')
```
///

#### Page size

If you're using `console` writer with `table` format option, you can specify
`page_size` parameter to print N rows to the console.

/// tab | cli
```bash hl_lines="3"
garf query.sql --source API_SOURCE \
  --output console \
  --console.page-size=100
```
///

/// tab | python
```python hl_lines="7"
from garf_core import report
from garf_io.writers import console_writer

# Create example report
sample_report = report.GarfReport(results=[[1]], column_names=['one'])

writer = console_writer.ConsoleWriter(page_size=100)
writer.write(sample_report, 'query')
```
///

### CSV

`csv` writer allows you to save `GarfReport` as a CSV file to local or remote storage.

/// tab | cli
```bash
garf query.sql --source API_SOURCE \
  --output csv
```
///

/// tab | python
```python
from garf_core import report
from garf_io.writers import csv_writer

# Create example report
sample_report = report.GarfReport(results=[[1]], column_names=['one'])

writer = csv_writer.CsvWriter()
writer.write(sample_report, 'query')
```
///

#### Destination folder

For `csv` writer you can specify the local or remote folder to store results.
I.e. if you want to write results to Google Cloud Storage bucket `gs://PROJECT_ID/bucket`,
you need to provide `destination_folder` parameter.


/// tab | cli
```bash hl_lines="3"
garf query.sql --source API_SOURCE \
  --output csv \
  --csv.destination-folder=gs://PROJECT_ID/bucket
```
///

/// tab | python
```python
from garf_core import report
from garf_io.writers import csv_writer

# Create example report
sample_report = report.GarfReport(results=[[1]], column_names=['one'])

writer = csv_writer.CsvWriter(destination_folder='gs://PROJECT_ID/bucket/')
writer.write(sample_report, 'query')
```
///

### JSON

`json` writer allows you to save `GarfReport` as JSON or JSONL file to local or remote storage.

/// tab | cli
```bash
garf query.sql --source API_SOURCE \
  --output json
```
///

/// tab | python
```python
from garf_core import report
from garf_io.writers import json_writer

# Create example report
sample_report = report.GarfReport(results=[[1]], column_names=['one'])

writer = json_writer.JsonWriter()
writer.write(sample_report, 'query')
```
///

#### Destination folder

You can specify the local or remote folder to store results.
I.e. if you want to write results to Google Cloud Storage bucket `gs://PROJECT_ID/bucket`,
you need to provide `destination_folder` parameter.


/// tab | cli
```bash hl_lines="3"
garf query.sql --source API_SOURCE \
  --output json \
  --json.destination-folder=gs://PROJECT_ID/bucket
```
///

/// tab | python
```python
from garf_core import report
from garf_io.writers import json_writer

# Create example report
sample_report = report.GarfReport(results=[[1]], column_names=['one'])

writer = json_writer.JsonWriter(destination_folder='gs://PROJECT_ID/bucket/')
writer.write(sample_report, 'query')
```
///

#### Format

You can specify the output format:

* `json` - JSON (default)
* `jsonl` - JSON lines

/// tab | cli
```bash hl_lines="3"
garf query.sql --source API_SOURCE \
  --output json \
  --json.format=jsonl
```
///

/// tab | python
```python hl_lines="7"
from garf_core import report
from garf_io.writers import json_writer

# Create example report
sample_report = report.GarfReport(results=[[1]], column_names=['one'])

writer = json_writer.JsonWriter(format='jsonl')
writer.write(sample_report, 'query')
```
///

### BigQuery

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

#### Project

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

#### Dataset

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

#### Location

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

#### Write disposition

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

### Google Sheets

!!! important
    To save data to Google Sheets install `garf-io` with Google Sheets support

    ```bash
    pip install garf-io[sheets]
    ```


`sheets` writer allows you to save `GarfReport` to Google Sheets.

/// tab | cli
```bash
garf query.sql --source API_SOURCE \
  --output sheets
```
///

/// tab | python
```python
from garf_core import report
from garf_io.writers import sheets_writer

# Create example report
sample_report = report.GarfReport(results=[[1]], column_names=['one'])

writer = sheets_writer.SheetsWriter()
writer.write(sample_report, 'query')
```
///

### SqlAlchemy

!!! important
    To save data to Google Sheets install `garf-io` with SqlAlchemy support

    ```bash
    pip install garf-io[sqlalchemy]
    ```


`sqldb` writer allows you to save `GarfReport` to SqlAlchemy supported table databases.

/// tab | cli
```bash
garf query.sql --source API_SOURCE \
  --output sqldb
```
///

/// tab | python
```python
from garf_core import report
from garf_io.writers import sqldb_writer

# Create example report
sample_report = report.GarfReport(results=[[1]], column_names=['one'])

writer = sqldb_writer.SqlAlchemyWriter(
  connection_string=SQLALCHEMY_CONNECTION_STRING
)
writer.write(sample_report, 'query')
```
///

## Configuration

Each of writer also support two options for dealing with arrays:

* `WRITER.array-handling` - arrays handling method: "strings" (default)  - store arrays as strings (items combined via a separator, e.g. "item1|item2"), "arrays" - store arrays as arrays.
* `WRITER.array-separator` - a separator symbol for joining arrays as strings, by default '|'.
