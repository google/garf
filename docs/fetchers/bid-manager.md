## garf for Bid Manager API

Interacts with [Bid Manager API](https://developers.google.com/bid-manager).

## Install

Install `garf-bid-manager` library

/// tab | pip
```
pip install garf-executors garf-bid-manager
```
///

/// tab | uv
```
uv pip install garf-executors garf-bid-manager
```
///

## Usage

### Prerequisites

* [Bid Manager API](https://console.cloud.google.com/apis/library/analytics.googleapis.com) enabled.
* [Credentials](https://developers.google.com/bid-manager/guides/get-started/generate-credentials) configured, can be exposed  as `GARF_BID_MANAGER_CREDENTIALS_FILE` ENV variable

/// tab | cli
```bash
echo """
SELECT
  advertiser,
  metric_clicks AS clicks
FROM standard
WHERE advertiser = 1
  AND dataRange = LAST_7_DAYS
  " > query.sql
garf query.sql --source bid-manager \
  --output csv
```
///

/// tab | python

```python
import os

from garf_io import writer
from garf_bid_manager import BidManagerApiReportFetcher

query = """
SELECT
  advertiser,
  metric_clicks AS clicks
FROM standard
WHERE advertiser = 1
  AND dataRange = LAST_7_DAYS
"""

fetched_report = (
  BidManagerApiReportFetcher(
    credentials_file=os.getenv('GARF_BID_MANAGER_CREDENTIALS_FILE')
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
| `credentials_file`   | File with Oauth or service account credentials | You can expose `credentials_file` as `GARF_BID_MANAGER_CREDENTIALS_FILE` ENV variable|
