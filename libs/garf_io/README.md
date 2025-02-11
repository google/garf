# `garf-io` - Writing GarfReport to anywhere

[![PyPI](https://img.shields.io/pypi/v/garf-io?logo=pypi&logoColor=white&style=flat-square)](https://pypi.org/project/garf-io)
[![Downloads PyPI](https://img.shields.io/pypi/dw/garf-io?logo=pypi)](https://pypi.org/project/garf-io/)

`garf-io` handles reading queries and writing `GarfReport` to various local/remote storages.

Currently it supports writing data to the following destination:

| identifier | Writer           | Options  |
|------------| ---------------- | -------- |
| `console`  | ConsoleWriter    | `page-size=10`,`format=table\|json`|
| `csv`      | CsvWriter        | `destination-folder` |
| `json`     | JsonWriter       | `destination-folder` |
| `bq`       | BigQueryWriter   | `project`, `dataset`, `location`, `write-disposition` |
| `sqldb`    | SqlAlchemyWriter | `connection-string`, `if-exists=fail\|replace\|append` |
| `sheets`   | SheetsWriter     | `share-with`, `credentials-file`, `spreadsheet-url`, `is_append=True\|False`|

## Installation

`pip install garf-io`

By default  `garf-io` has only support for `console`, `csv` and `json` writers.\
To install all writers use the following command `pip install garf-io[all]`.\
To install specific writers use:
* `pip install garf-io[bq]` for BigQuery support
* `pip install garf-io[sheets]` for Google spreadsheets support
* `pip install garf-io[sqlalchemy]` for SqlAlchemy support
## Usage

```
import garf_core import report
from garf_io import writer

# Create example report
sample_report = report.GarfReport(results=[[1]], column_names=['one'])

# Initialize CSV writer
concrete_writer = writer.create_writer('csv', destination_folder='/tmp/')

# Write data to /tmp/sample.csv
concrete_writer.write(sample_report, 'sample')
```
