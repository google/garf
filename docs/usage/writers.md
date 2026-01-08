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
from garf_core import report
from garf_io import writer

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

Each of writer also support two options for dealing with arrays:

* `WRITER.array-handling` - arrays handling method: "strings" (default)  - store arrays as strings (items combined via a separator, e.g. "item1|item2"), "arrays" - store arrays as arrays.
* `WRITER.array-separator` - a separator symbol for joining arrays as strings, by default '|'.
