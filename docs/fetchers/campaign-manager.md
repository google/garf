## garf for Campaign Manager 360 API

[![PyPI](https://img.shields.io/pypi/v/garf-campaign-manager?logo=pypi&logoColor=white&style=flat-square)](https://pypi.org/project/garf-campaign-manager)
[![Downloads PyPI](https://img.shields.io/pypi/dw/garf-campaign-manager?logo=pypi)](https://pypi.org/project/garf-campaign-manager/)

Interacts with [Campaign Manager 360 API](https://developers.google.com/doubleclick-advertisers).

## Install

Install `garf-campaign-manager` library

/// tab | pip
```
pip install garf-executors garf-campaign-manager
```
///

/// tab | uv
```
uv pip install garf-executors garf-campaign-manager
```
///

## Usage

### Prerequisites

* [Campaign Manager 360 API](https://console.cloud.google.com/apis/library/dfareporting.googleapis.com) enabled.
* [Credentials](https://developers.google.com/campaign-manager/guides/get-started/generate-credentials) configured, can be exposed  as `GARF_CAMPAIGN_MANAGER_360_CREDENTIALS_FILE` ENV variable

/// tab | cli
```bash
echo """
SELECT
  dimensions.advertiser AS advertiser,
  advertiserId AS advertiser_id,
  metric.clicks AS clicks
FROM standard
WHERE
  dateRange IN (2025-01-01, 2025-12-31)
" > query.sql
garf query.sql --source campaign-manager \
  --output csv --campaign-manager.profile-id=<PROFILE_ID>
```
///

/// tab | python

```python
import os

from garf.io import writer
from garf.community.google.campaign_manager import CampaignManager360ApiReportFetcher

query = """
SELECT
  dimensions.advertiser AS advertiser,
  advertiserId AS advertiser_id,
  metric.clicks AS clicks
FROM standard
WHERE
  dateRange IN (2025-01-01, 2025-12-31)
"""

fetched_report = (
  CampaignManager360ApiReportFetcher(
    credentials_file=os.getenv('GARF_CAMPAIGN_MANAGER_360_CREDENTIALS_FILE'),
    profile_id=<PROFILE_ID>,
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
| `profile_id`   | Id of CM360 profile | |
| `credentials_file`   | File with Oauth or service account credentials | You can expose `credentials_file` as `GARF_CAMPAIGN_MANAGER_360_CREDENTIALS_FILE` ENV variable|
| `auth_mode`   | Type of authentication: `oauth` or `service_account` | `oauth` is the default mode|

## Query syntax

`garf-campaign-manager` uses simplified syntax for writing queries.

* To differentiate between metrics and dimension add `dimensions.` or `metrics.` prefix before corresponding dimension / metric name. If prefix is omitted the name is treated as a dimension.
