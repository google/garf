# `garf` for Prometheus HTTP API

[![PyPI](https://img.shields.io/pypi/v/garf-prometheus?logo=pypi&logoColor=white&style=flat-square)](https://pypi.org/project/garf-prometheus)
[![Downloads PyPI](https://img.shields.io/pypi/dw/garf-prometheus?logo=pypi)](https://pypi.org/project/garf-prometheus/)

`garf-prometheus` simplifies fetching data from Prometheus HTTP API using SQL-like queries.

## Prerequisites

* Running Prometheus instance

## Installation

`pip install garf-prometheus`

## Usage

### Run as a library
```
import os

from garf.io import writer
from garf.community.prometheus import PrometheusApiReportFetcher

query = """
SELECT
  timestamp,
  instance,
  job,
  value
FROM query
WHERE query = up
"""

fetched_report = (
  PrometheusApiReportFetcher(
    endpoint='http://localhost:9090'
  )
  .fetch(query)
)

console_writer = writer.create_writer('console')
console_writer.write(fetched_report, 'query')
```

### Run via CLI

> Install `garf-executors` package to run queries via CLI (`pip install garf-executors`).

```
garf <PATH_TO_QUERIES> --source prometheus \
  --output <OUTPUT_TYPE> \
  --prometheus.endpoint=http://localhost:9090
```

where:

* `PATH_TO_QUERIES` - local or remove files containing queries
* `output` - output supported by [`garf-io` library](https://google.github.io/garf/usage/writers/).
* `SOURCE_PARAMETER=VALUE` - key-value pairs to refine fetching, check [available source parameters](#available-source-parameters).

###  Available source parameters

| name | values| comments |
|----- | ----- | -------- |
| `endpoint`   | Base URL when Prometheus is running (`http://localhost:9090` by default) |

## Documentation

You can find a documentation on `garf-prometheus` [here](https://google.github.io/garf/fetchers/prometheus/).
