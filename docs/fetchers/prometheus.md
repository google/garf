## garf for Prometheus HTTP API

[![PyPI](https://img.shields.io/pypi/v/garf-prometheus?logo=pypi&logoColor=white&style=flat-square)](https://pypi.org/project/garf-prometheus)
[![Downloads PyPI](https://img.shields.io/pypi/dw/garf-prometheus?logo=pypi)](https://pypi.org/project/garf-prometheus/)

`garf-prometheus` simplifies fetching data from [Prometheus HTTP API](https://prometheus.io/docs/prometheus/latest/querying/api/) using SQL-like queries.

## Install

Install `garf-prometheus` library

/// tab | pip
```
pip install garf-executors garf-prometheus
```
///

/// tab | uv
```
uv pip install garf-executors garf-prometheus
```
///

## Usage

### Prerequisites

* Running Prometheus instance

/// tab | cli
```bash
echo """
SELECT
  timestamp,
  job,
  instance,
  value
FROM query
WHERE
  query = up
" > query.sql
garf query.sql --source prometheus \
  --output csv --prometheus.endpoint=http://localhost:9090
```
///

/// tab | python

```python
import os

from garf.io import writer
from garf.community.prometheus import PrometheusApiReportFetcher

query = """
SELECT
  timestamp,
  job,
  instance,
  value
FROM query
WHERE
  query = up
"""

fetched_report = (
  PrometheusApiReportFetcher(
    endpoint='http://localhost:9090'
  )
  .fetch(query)
)

csv_writer = writer.create_writer('csv')
csv_writer.write(fetched_report, 'query')
```
///

###  Available source parameters

| name | values| comments |
|----- | ----- | -------- |
| `endpoint`   | Base URL when Prometheus is running (`http://localhost:9090` by default) |
