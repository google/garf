# `garf` for Google Ads  & Search Ads 360 API

[![PyPI](https://img.shields.io/pypi/v/garf-google-ads?logo=pypi&logoColor=white&style=flat-square)](https://pypi.org/project/garf-google-ads)
[![Downloads PyPI](https://img.shields.io/pypi/dw/garf-google-ads?logo=pypi)](https://pypi.org/project/garf-google-ads/)

`garf-google-ads` simplifies fetching data from Google Ads & Search Ads 360 API using SQL-like queries.

## Prerequisites

* [Google Ads API](https://console.cloud.google.com/apis/library/googleads.googleapis.com) enabled.
* (Optional) [Search Ads 360 API](https://console.cloud.google.com/apis/library/doubleclicksearch.googleapis.com) enabled if you want to interact with Search Ads 360 API.


## Installation

`pip install garf-google-ads`

> To work with Search Ads 360 API install run `pip install garf-google-ads[search-ads-360]`

## Usage

### Run as a library
```
import os

from garf.io import writer
from garf.community.google.ads import GoogleAdsApiReportFetcher

query = """
SELECT
  campaign.id,
  metrics.clicks AS clicks
FROM campaign
WHERE segments.date DURING LAST_7_DAYS
"""

fetched_report = (
  GoogleAdsApiReportFetcher(
    path_to_config=os.getenv('GOOGLE_ADS_CONFIGURATION_FILE_PATH')
  )
  .fetch(query, account=os.getenv('GOOGLE_ADS_ACCOUNT'))
)

console_writer = writer.create_writer('console')
console_writer.write(fetched_report, 'query')
```

### Run via CLI

> Install `garf-executors` package to run queries via CLI (`pip install garf-executors`).

```
garf <PATH_TO_QUERIES> --source google-ads \
  --output <OUTPUT_TYPE> \
  --source.account=GOOGLE_ADS_ACCOUNT \
  --source.path-to-config=./google-ads.yaml
```

where:

* `PATH_TO_QUERIES` - local or remove files containing queries
* `output` - output supported by [`garf-io` library](https://google.github.io/garf/usage/writers/).
* `SOURCE_PARAMETER=VALUE` - key-value pairs to refine fetching, check [available source parameters](#available-source-parameters).

###  Available source parameters

| name | values| comments |
|----- | ----- | -------- |
| `account`   | Account(s) to get data from | Can be MCC(s) as well |
| `path-to-config`   | Path to `google-ads.yaml` file | `~/google-ads.yaml` is a default location |
| `expand-mcc`   | Whether to force account expansion if MCC is provided | `False` by default |
| `customer-ids-query`   | Optional query to find account satisfying specific condition | |
| `version`   | Version of Google Ads API |  |

## Documentation

You can find a documentation on `garf-google-ads` [here](https://google.github.io/garf/fetchers/google-ads/).
