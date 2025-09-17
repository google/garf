# garf for Google Analytics Data API

[![PyPI](https://img.shields.io/pypi/v/garf-google-analytics?logo=pypi&logoColor=white&style=flat-square)](https://pypi.org/project/garf-google-analytics)
[![Downloads PyPI](https://img.shields.io/pypi/dw/garf-google-analytics?logo=pypi)](https://pypi.org/project/garf-google-analytics/)

Interacts with [Google Analytics Data API](https://developers.google.com/analytics/devguides/reporting/data/v1/rest).

## Install

Install `garf-google-analytics` library

/// tab | pip
```
pip install garf-executors garf-google-analytics
```
///

/// tab | uv
```
uv add garf-executors garf-google-analytics
```
///

## Usage

### Prerequisites

* [Google Analytics API](https://console.cloud.google.com/apis/library/analytics.googleapis.com) enabled.


/// tab | cli
```bash
echo "
SELECT
  dimension.country AS country,
  metric.activeUsers AS active_users
FROM resource
WHERE
  start_date >= '2025-09-01'
  AND end_date <= '2025-09-07'
" > query.sql
garf query.sql --source google-analytics \
  --output csv \
  --source.property-id=GA_PROPERTY_ID
```
///

/// tab | python

```python
from garf_io import writer
from garf_google_analytics import GoogleAnalyticsApiReportFetcher

query = """
SELECT
  dimension.country AS country,
  metric.activeUsers AS active_users
FROM resource
WHERE
  start_date >= '2025-09-01'
  AND end_date <= '2025-09-07'
"""

fetched_report = (
  GoogleAnalyticsApiReportFetcher()
  .fetch(query, property_id='PROPERTY_ID')
)

csv_writer = writer.create_writer('csv')
csv_writer.write(fetched_report, 'query')
```
///
