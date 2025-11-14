# `garf` for Bid Manager API

[![PyPI](https://img.shields.io/pypi/v/garf-bid-manager?logo=pypi&logoColor=white&style=flat-square)](https://pypi.org/project/garf-bid-manager)
[![Downloads PyPI](https://img.shields.io/pypi/dw/garf-bid-manager?logo=pypi)](https://pypi.org/project/garf-bid-manager/)

`garf-bid-manager` simplifies fetching data from Bid Manager API using SQL-like queries.

## Prerequisites

* [Bid Manager API](https://console.cloud.google.com/apis/library/analytics.googleapis.com) enabled.
* [Credentials](https://developers.google.com/bid-manager/guides/get-started/generate-credentials) configured.

## Installation

`pip install garf-bid-manager`

## Usage

### Run as a library
```
import garf_bid_manager
from garf_io import writer

# Fetch report
query = """
  SELECT
    advertiser_name,
    metric_clicks AS clicks
  FROM standard
  WHERE advertiser = 1
    AND dataRange IN (2025-01-01, 2025-12-31)
"""
fetched_report = (
  garf_bid_manager.BidManagerApiReportFetcher()
  .fetch(query, query=query)
)

# Write report to console
console_writer = writer.create_writer('console')
console_writer.write(fetched_report, 'output')
```

### Run via CLI

> Install `garf-executors` package to run queries via CLI (`pip install garf-executors`).

```
garf <PATH_TO_QUERIES> --source bid-manager \
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
| `credentials_file`   | File with Oauth or service account credentials | You can expose `credentials_file` as `GARF_BID_MANAGER_CREDENTIALS_FILE` ENV variable|
| `auth_mode`   | Type of authentication: `oauth` or `service_account` | `oauth` is the default mode|
