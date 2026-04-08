## garf for Google Ads & Search Ads 360 API

[![PyPI](https://img.shields.io/pypi/v/garf-google-ads?logo=pypi&logoColor=white&style=flat-square)](https://pypi.org/project/garf-google-ads)
[![Downloads PyPI](https://img.shields.io/pypi/dw/garf-google-ads?logo=pypi)](https://pypi.org/project/garf-google-ads/)

Interacts with [Google Ads API](https://developers.google.com/google-ads-api) and [Search Ads 360 API](https://developers.google.com/search-ads/reporting).

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

## Google Ads

### Prerequisites

* [Google Ads API](https://console.cloud.google.com/apis/library/googleads.googleapis.com) enabled.
* `google-ads.yaml` file

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

### Built-in queries

`garf-google-ads` supports several [built-in queries](../usage/queries.md#built-in-queries):

#### ocid_mapping

Returns mapping between `account_id` and `ocid` parameter
that used to provide deep links to Google Ads UI.

Returned columns:

* `account_id` - Id of Google Ads Account.
* `ocid` - linking parameter.

#### budget_history

Returns table with historical budgets for each campaign_id for each day
for the previous 28 days.

Returned columns:

* `day` - Day.
* `campaign_id` - Id of campaign.
* `budget_amount` - Budget amount in micros for a given day and campaign.

#### target_cpa_history

Returns table with historical target_cpas for each campaign_id with TARGET_CPA
bidding_strategy_type for each day for the previous 28 days.

Returned columns:

* `day` - Day.
* `campaign_id` - Id of campaign.
* `target_cpa` - Budget amount in micros for a given day and campaign.

#### target_roas_history

Returns table with historical target_ROAS for each campaign_id with TARGET_ROAS
bidding_strategy_type for each day for the previous 28 days.

Returned columns:

* `day` - Day.
* `campaign_id` - Id of campaign.
* `target_roas` - Budget amount in micros for a given day and campaign.


## Search Ads 360

!!!note
    Install extra dependency to work with Search Ads 360 API
    ```
    pip install garf-google-ads[search-ads-360]
    ```

### Prerequisites

* [Search Ads 360 API](https://console.cloud.google.com/apis/library/doubleclicksearch.googleapis.com) enabled.
* `search-ads-360.yaml` file.

/// tab | cli
```bash
echo """
SELECT
  campaign.id,
  metrics.clicks AS clicks
FROM campaign
WHERE segments.date DURING LAST_7_DAYS
  " > query.sql
garf query.sql --source search-ads-360 \
  --output console
```
///

/// tab | python

```python
import os

from garf.io import writer
from garf.community.google.ads import SearchAds360ApiReportFetcher

query = """
SELECT
  campaign.id,
  metrics.clicks AS clicks
FROM campaign
WHERE segments.date DURING LAST_7_DAYS
"""

fetched_report = (
  SearchAds360ApiReportFetcher(
    path_to_config=os.getenv('SEARCH_ADS_360_CONFIGURATION_FILE_PATH')
  )
  .fetch(query, account=os.getenv('SEARCH_ADS_360_ACCOUNT'))
)

console_writer = writer.create_writer('console')
console_writer.write(fetched_report, 'query')
```
///

###  Available source parameters

| name | values| comments |
|----- | ----- | -------- |
| `account`   | Account(s) to get data from | Can be MCC(s) as well |
| `path-to-config`   | Path to `search-ads-360.yaml` file | `~/search-ads-360.yaml` is a default location |
| `expand-mcc`   | Whether to force account expansion if MCC is provided | `False` by default |
| `customer-ids-query`   | Optional query to find account satisfying specific condition | |
