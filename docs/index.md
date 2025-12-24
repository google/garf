# garf - Python library for interacting with reporting APIs

## What is garf?

`garf` is a Python library for building various connectors to reporting API that provides
users with a SQL-like interface to specify what needs to be extracted from the API.

Write a query and  `garf` will do the rest- build the correct request to an API, parse response
and writes it virtually anywhere.

## Key features


* Rich [SQL-like syntax](usage/queries.md) to interact with reporting APIs.
* Built-in support for [writing data](usage/writers.md) into various local / remote storage.
* Easily [extendable](development/overview.md) to support various APIs.
* Built-in support for post-processing saved data in [BigQuery](usage/bq-executor.md) & [SQL](usage/sql-executor.md) databases.
* Available as library, CLI, FastAPI endpoint.

## Supported APIs

* [YouTube Data API](fetchers/youtube-data-api.md)
* [YouTube Reporting API](fetchers/youtube-reporting-api.md)
* [Google Analytics](fetchers/google-analytics-api.md)
* [Google Merchant Center](fetchers/merchant-center-api.md)
* [Google Ads](fetchers/google-ads.md)

## Installation

/// tab | pip
```bash
pip install garf-executors
```
///

/// tab | uv
```bash
uv add garf-executors
```
///


## Usage

### CLI

```bash
echo 'SELECT id, name AS model, data.color AS color FROM objects' > query.sql
garf  query.sql --source rest --source.endpoint=https://api.restful-api.dev
```

### Python library

```python
from garf_core.report_fetcher import ApiReportFetcher
from garf_core.api_clients import RestApiClient
from garf_io import writer

api_client = RestApiClient(endpoint='https://api.restful-api.dev')
fetcher = ApiReportFetcher(api_client)
query = 'SELECT id, name AS model, data.color AS color FROM objects'
report = fetcher.fetch(query)

# Convert to Pandas
report.to_pandas()

# Write to CSV
writer.create_writer('console').write(report, 'api_data')
```
