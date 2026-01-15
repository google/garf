## garf for Google Ads API

[![PyPI](https://img.shields.io/pypi/v/garf-google-ads?logo=pypi&logoColor=white&style=flat-square)](https://pypi.org/project/garf-google-ads)
[![Downloads PyPI](https://img.shields.io/pypi/dw/garf-google-ads?logo=pypi)](https://pypi.org/project/garf-google-ads/)

Interacts with [Google Ads API](https://developers.google.com/google-ads-api).

## Install

Install `garf-google-ads` library

/// tab | pip
```
pip install garf-executors garf-google-ads
```
///

/// tab | uv
```
uv pip install garf-executors garf-google-ads
```
///

## Usage

### Prerequisites

* [Google Ads API](https://console.cloud.google.com/apis/library/googleads.googleapis.com) enabled.

/// tab | cli
```bash
echo """
SELECT
  campaign.id,
  metrics.clicks AS clicks
FROM campaign
WHERE segments.date DURING LAST_7_DAYS
  " > query.sql
garf query.sql --source google-ads \
  --output console
```
///

/// tab | python

```python
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
///

###  Available source parameters

| name | values| comments |
|----- | ----- | -------- |
| `account`   | Account(s) to get data from | Can be MCC(s) as well |
| `path-to-config`   | Path to `google-ads.yaml` file | `~/google-ads.yaml` is a default location |
| `expand-mcc`   | Whether to force account expansion if MCC is provided | `False` by default |
| `customer-ids-query`   | Optional query to find account satisfying specific condition | |
| `version`   | Version of Google Ads API |  |
