# `garf` for Display & Video 360 API

[![PyPI](https://img.shields.io/pypi/v/garf-dv360-api?logo=pypi&logoColor=white&style=flat-square)](https://pypi.org/project/garf-dv360-api)
[![Downloads PyPI](https://img.shields.io/pypi/dw/garf-dv360-api?logo=pypi)](https://pypi.org/project/garf-dv360-api/)

`garf-dv360-api` simplifies fetching data from Merchant API using SQL-like queries.

## Prerequisites

* [Merchant API](https://console.cloud.google.com/apis/library/dv360api.googleapis.com) enabled.

## Installation

`pip install garf-dv360-api`

## Usage

### Run as a library
```
from garf_dv360_api import report_fetcher
from garf_io import writer


# Specify query
query = """
  SELECT
    date,
    clicks
    FROM product_performance_view
    WHERE date BETWEEN '2023-12-01' AND '2023-12-03'
  ORDER BY clicks DESC
""

# Fetch report
fetched_report = (
  report_fetcher.DV360ApiReportFetcher()
  .fetch(query, query="<YOUR_SEARCH_QUERY_HERE">, account=ACCOUNT_ID)
)

# Write report to console
console_writer = writer.create_writer('console')
console_writer.write(fetched_report, 'output')
```

### Run via CLI

> Install `garf-executors` package to run queries via CLI (`pip install garf-executors`).

```
garf <PATH_TO_QUERIES> --source dv360-api \
  --output <OUTPUT_TYPE> \
  --source.<SOURCE_PARAMETER=VALUE>
```

where:

* `<PATH_TO_QUERIES>` - local or remove files containing queries
* `<OUTPUT_TYPE>` - output supported by [`garf-io` library](../garf_io/README.md).
* `<SOURCE_PARAMETER=VALUE` - key-value pairs to refine fetching, check [available source parameters](#available-source-parameters).

## Available source parameters

| name | values| comments |
|----- | ----- | -------- |
| `account`   | Account(s) to get data to | Multiple accounts are supported, should be comma-separated|
