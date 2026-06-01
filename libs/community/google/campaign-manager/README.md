# `garf` for Campaign Manager 360 API

[![PyPI](https://img.shields.io/pypi/v/garf-campaign-manager?logo=pypi&logoColor=white&style=flat-square)](https://pypi.org/project/garf-campaign-manager)
[![Downloads PyPI](https://img.shields.io/pypi/dw/garf-campaign-manager?logo=pypi)](https://pypi.org/project/garf-campaign-manager/)

`garf-campaign-manager` simplifies fetching data from Campaign Manager 360 API using SQL-like queries.

## Prerequisites

* [Campaign Manager 360 API](https://console.cloud.google.com/apis/library/dfareporting.googleapis.com) enabled.
* [Credentials](https://developers.google.com/campaign-manager/guides/get-started/generate-credentials) configured.

## Installation

`pip install garf-campaign-manager`

## Usage

### Run as a library
```
from garf.community.google.campaign_manager import CampaignManager360ApiReportFetcher
from garf.io import writer

# Fetch report
query = """
  SELECT
    dimensions.advertiser AS advertiser,
    advertiserId AS advertiser_id,
    metric.clicks AS clicks
  FROM standard
  WHERE
    dateRange IN (2025-01-01, 2025-12-31)
"""
fetched_report = CampaignManager360ApiReportFetcher(profile_id=<PROFILE_ID>).fetch(query, title='sample_query')

# Write report to console
console_writer = writer.create_writer('console')
console_writer.write(fetched_report, 'output')
```

### Run via CLI

> Install `garf-executors` package to run queries via CLI (`pip install garf-executors`).

```
garf <PATH_TO_QUERIES> --source campaign-manager \
  --output <OUTPUT_TYPE> \
  --source.<SOURCE_PARAMETER=VALUE>
```

where:

* `<PATH_TO_QUERIES>` - local or remove files containing queries
* `output` - output supported by [`garf-io` library](https://google.github.io/garf/usage/writers/).
* `<SOURCE_PARAMETER=VALUE` - key-value pairs to refine fetching, check [available source parameters](#available-source-parameters).

## Available source parameters

| name | values| comments |
|----- | ----- | -------- |
| `profile_id`   | Id of CM360 profile | |
| `credentials_file`   | File with Oauth or service account credentials | You can expose `credentials_file` as `GARF_CAMPAIGN_MANAGER_360_CREDENTIALS_FILE` ENV variable|
| `auth_mode`   | Type of authentication: `oauth` or `service_account` | `oauth` is the default mode|
