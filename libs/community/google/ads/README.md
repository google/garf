# `garf` for Google Ads API

[![PyPI](https://img.shields.io/pypi/v/garf-google-ads?logo=pypi&logoColor=white&style=flat-square)](https://pypi.org/project/garf-google-ads)
[![Downloads PyPI](https://img.shields.io/pypi/dw/garf-google-ads?logo=pypi)](https://pypi.org/project/garf-google-ads/)

`garf-google-ads` simplifies fetching data from Google Ads API using SQL-like queries.

## Prerequisites

* [Google Ads API](https://console.cloud.google.com/apis/library/googleads.googleapis.com) enabled.

## Installation

`pip install garf-google-ads`

## Usage

### Run as a library
```
import garf_google_ads
from garf_io import writer

# Fetch report
query = """
  SELECT
    campaign.id AD campaign_id,
    campaign.name AS campaign
  FROM campaign
  WHERE
    campaign.status = ENABLED
"""
fetched_report = (
  garf_google_ads.GoogleAdsApiReportFetcher()
  .fetch(query, query=query)
)

# Write report to console
console_writer = writer.create_writer('console')
console_writer.write(fetched_report, 'output')
```

### Run via CLI

> Install `garf-executors` package to run queries via CLI (`pip install garf-executors`).

```
garf <PATH_TO_QUERIES> --source google-ads \
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
| `account`   | Google Ads Account to get data from | |
| `path_to_config`   | Path to `google-ads.yaml` | |
