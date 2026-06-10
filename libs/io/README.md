# `garf-io` - Writing GarfReport to anywhere

[![PyPI](https://img.shields.io/pypi/v/garf-io?logo=pypi&logoColor=white&style=flat-square)](https://pypi.org/project/garf-io)
[![Downloads PyPI](https://img.shields.io/pypi/dw/garf-io?logo=pypi)](https://pypi.org/project/garf-io/)

`garf-io` handles reading queries and writing `GarfReport` to various local/remote storages.

## Installation

```
pip install garf-io
```
By default  `garf-io` has only support for `console`, `csv` and `json` writers -
explore what [additional writers are available](https://google.github.io/garf/usage/writers).


## Usage

### CLI

```
garf query.sql --source API_SOURCE \
  --output csv --csv.destination-folder=/tmp/
```
### Python

```python
import garf.core import report
from garf.io import writer

# Create example report
sample_report = report.GarfReport(results=[[1]], column_names=['one'])

# Initialize CSV writer
concrete_writer = writer.create_writer('csv', destination_folder='/tmp/')

# Write data to /tmp/sample.csv
concrete_writer.write(sample_report, 'sample')
```

## Documentation

[Learn more](https://google.github.io/garf/usage/writers) about using `garf` writers.
