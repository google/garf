# garf - Framework for interacting with reporting APIs

`garf` is a framework for building various connectors to reporting API that provides
users with a SQL-like interface to specify what needs to be extracted from the API.

It allows you to define SQL-like queries alongside aliases and custom extractors and specify where the results of such query should be stored.\
Based on a query `garf` builds the correct request to a reporting API, parses response
and transform it into a structure suitable for writing data.

## Key features

* SQL-like syntax to interact with reporting APIs
* Built-in support for writing data into various local / remote storage
* Available as library, CLI, FastAPI endpoint
* Easily extendable to support various APIs


## Installation

```bash
pip install garf-executors
```


## Usage

### Get data from API to use in your code

```python
from garf_core import ApiReportFetcher
from garf_core.api_clients import FakeApiClient
from garf_io import writer

my_api_client = FakeApiClient(results=[{'field': 1}])
fetcher = ApiReportFetcher(my_api_client)
report = fetcher.fetch('SELECT field FROM resource_name')

# Convert to Pandas
report.to_pandas()

# Write to CSV
writer.create_writer('csv').write(report, 'api_data')

```

### Use `garf` CLI tool to fetch data from an API


```bash
garf /path/to/queries \
  --source youtube --source.channel=MY_CHANNEL_ID \
  --output csv
```

## Documentation

Explore full documentation on using and extending `garf`

* [Documentation](https://google.github.io/garf/)

## Disclaimer
This is not an officially supported Google product. This project is not
eligible for the [Google Open Source Software Vulnerability Rewards
Program](https://bughunters.google.com/open-source-security).
