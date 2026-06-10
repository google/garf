# Overview

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
| `elasticsearch`| ElasticsearchWriter| `hosts` |
| `excel`    | ExcelWriter      | `destination-folder`, `file` |
| `kafka`    | KafkaWriter      | `bootstrap-servers` |
| `opensearch`| OpenSearchWriter | `hosts` |
| `pubsub`   | PubSubWriter     | `project` |
| `mongo`    | MongoDbWriter     | `connection_string`, `db` |
| `firestore`   | FirestoreWriter     | `project`, `db` |


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
* `pip install garf-io[elasticsearch]` for Elasticsearch support
* `pip install garf-io[excel]` for Excel support
* `pip install garf-io[kafka]` for Kafka support
* `pip install garf-io[opensearch]` for OpenSearch support
* `pip install garf-io[pubsub]` for PubSub support
* `pip install garf-io[mongo]` for MongoDB support
* `pip install garf-io[firestore]` for Firestore support


## Usage

/// tab | cli
```bash
garf query.sql --source API_SOURCE \
  --output YOUR_WRITER
```

!!!note
    To use `cli` example you need to have `garf-executors` package installed.

    ```bash
    pip install garf-executors
    ```
///

/// tab | python
```python
from garf.core import report
from garf.io import writer

# Create example report
sample_report = report.GarfReport(results=[[1]], column_names=['one'])

concrete_writer = writer.create_writer('YOUR_WRITER')
concrete_writer.write(sample_report, 'query')
```

!!!note
    You can use `awrite` method to write report asynchronously.
    ```python
    await concrete_writer.awrite(sample_report, 'query')
    ```
///

## Configuration

### arrays

Each of writer also support two options for dealing with arrays:

* `WRITER.array_handling` - arrays handling method:
    * `strings` (default)  - store arrays as strings (items combined via a separator, e.g. "item1|item2")
    * `arrays` - store arrays as arrays.
* `WRITER.array_separator` - a separator symbol for joining arrays as strings, by default '|'.

/// tab | cli
```bash
garf query.sql --source API_SOURCE \
  --output json \
  --json.array-handling=arrays

garf query.sql --source API_SOURCE \
  --output json \
  --json.array-handling=strings --json.array-separator='*'
```
///

/// tab | python
```python
from garf.io.writers import json_writer


array_writer = json_writer.JsonWriter(array_handling='arrays')
string_writer = json_writer.JsonWriter(
  array_handling='strings', array_separator='*'
)

```

### dates

By default `garf` writes all date objects as strings. You can overwrite this with two options:

* `WRITER.date_handling` - specifies ways of handling date object:
    * `strings` (default)  - keeps date objects as strings .
    * `date` - formats date objects to proper dates.
    * `datetimes` - formats date objects to proper datetimes.
    * `timestamps` - formats date objects to proper timestamps.
* `WRITER.date_format_string` - specifies [format string](https://docs.python.org/3/library/datetime.html#format-codes).

/// tab | cli
```bash
garf query.sql --source API_SOURCE \
  --output bq \
  --bq.date-handling=dates

garf query.sql --source API_SOURCE \
  --output bq \
  --bq.date-handling=dates --json.date-format-string='%d/%m/%y'
```
///

/// tab | python
```python
from garf.io.writers import bigquery_writer


dates_writer = bigquery_writer.BigQueryWriter(date_handling='dates')
dates_writer_with_format = bigquery_writer.BigQueryWriter(
  date_handling='dates',
  date_format_string='%d/%m/%y',
)
```

### prefix / suffix

When writing data with `garf` you can use `prefix` and `suffix` to dynamically
update where (table / file / topic / index) data are written:

/// tab | cli
```bash
# Saves results to `my_prefix_query.csv'
garf query.sql --source API_SOURCE \
  --output csv \
  --csv.prefix=my_prefix

# Saves results to `query_my_suffix.csv'
garf query.sql --source API_SOURCE \
  --output csv \
  --csv.suffix=my_suffix

# Saves results to `my_prefix_query_my_suffix.csv'
garf query.sql --source API_SOURCE \
  --output csv \
  --csv.prefix=my_prefix \
  --csv.suffix=my_suffix
```
///

/// tab | python
```python
from garf.io.writers import csv_writer

# Saves results to `my_prefix_query_my_suffix.csv'
writer = csv_writer.CsvWriter(prefix='my_prefix', suffix='my_suffix')
```
