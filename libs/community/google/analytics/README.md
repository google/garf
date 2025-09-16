# `garf` for Google Analytics API

[![PyPI](https://img.shields.io/pypi/v/garf-google-analytics?logo=pypi&logoColor=white&style=flat-square)](https://pypi.org/project/garf-google-analytics)
[![Downloads PyPI](https://img.shields.io/pypi/dw/garf-google-analytics?logo=pypi)](https://pypi.org/project/garf-google-analytics/)

`garf-google-analytics` simplifies fetching data from Google Analytics API using SQL-like queries.

## Prerequisites

* [Google Analytics API](https://console.cloud.google.com/apis/library/analytics.googleapis.com) enabled.

## Installation

`pip install garf-google-analytics`

## Usage

### Run as a library
```
import garf_google_analytics
from garf_io import writer

# Fetch report
fetched_report = (
  garf_google_analytics.GoogleAnalyticsApiReportFetcher()
  .fetch(query, query="<YOUR_QUERY_HERE">, property_id=PROPERTY_ID)
)

# Write report to console
console_writer = writer.create_writer('console')
console_writer.write(fetched_report, 'output')
```

### Run via CLI

> Install `garf-executors` package to run queries via CLI (`pip install garf-executors`).

```
garf <PATH_TO_QUERIES> --source google-analytics \
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
| `property_id`   | Property to get data to | Multiple properties are supported, should be comma-separated|
