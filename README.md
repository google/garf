# garf - Python library for interacting with reporting APIs

`garf` is a Python library for building various connectors to reporting API that provides
users with a SQL-like interface to specify what needs to be extracted from the API.

Write a query and  `garf` will do the rest- build the correct request to an API, parse response
and writes it virtually anywhere.

## Key features

* Rich [SQL-like syntax](https://google.github.io/garf/usage/queries/) to interact with reporting APIs.
* Built-in support for [writing data](https://google.github.io/garf/usage/writers/) into various local / remote storage.
* Built-in support for post-processing saved data in [BigQuery](https://google.github.io/garf/usage/bq-executor/) & [SQL](https://google.github.io/garf/usage/sql-executor/) databases.
* Easily [extendable](https://google.github.io/garf/development/overview/) to support various APIs.
* Available as library, CLI, FastAPI endpoint.


## Supported APIs

* [YouTube Data API](https://google.github.io/garf/fetchers/youtube-data-api/)
* [YouTube Reporting API](https://google.github.io/garf/fetchers/youtube-reporting-api/)
* [Google Analytics](https://google.github.io/garf/fetchers/google-analytics-api/)
* [Google Merchant Center](https://google.github.io/garf/fetchers/merchant-center-api/)


## Installation

```bash
pip install garf-executors
```

## Usage

### Use `garf` CLI tool to fetch data from an API

```bash
echo 'SELECT id, name AS model, data.color AS color FROM objects' > query.sql
garf  query.sql --source rest --source.endpoint=https://api.restful-api.dev
```

### Get data from API to use in your code

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


## Documentation

Explore full documentation on using and extending `garf`

* [Documentation](https://google.github.io/garf/)

## Disclaimer
This is not an officially supported Google product. This project is not
eligible for the [Google Open Source Software Vulnerability Rewards
Program](https://bughunters.google.com/open-source-security).
