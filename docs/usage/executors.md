# Overview

[![PyPI](https://img.shields.io/pypi/v/garf-executors?logo=pypi&logoColor=white&style=flat-square)](https://pypi.org/project/garf-executors)
[![Downloads PyPI](https://img.shields.io/pypi/dw/garf-executors?logo=pypi)](https://pypi.org/project/garf-executors/)

`garf-executors` is responsible for orchestrating process of fetching from API and storing data in a storage.

Currently the following executors are supported:

* [`ApiExecutor`](api-executor.md) - fetching data from reporting API and saves it to a requested destination.
* [`BigQueryExecutor`](bq-executor.md) - executes SQL code in BigQuery.
* [`SqlExecutor`](sql-executor.md) - executes SQL code in a SqlAlchemy supported DB.

## Installation

/// tab | api
```bash
pip install garf-executors
```
///

/// tab | bigquery
```bash
pip install garf-executors[bq]
```
///

/// tab | sqlalchemy
```bash
pip install garf-executors[sql]
```
///

## Usage

After `garf-executors` is installed you can use `garf` utility to perform fetching.

/// tab | cli
```bash
garf <QUERIES> --source <API_SOURCE> \
  --output <OUTPUT_TYPE> \
  --source.params1=<VALUE>
```

where

* `query` - local or remote path(s) to files with queries.
* `source`- type of API to use. Based on that the appropriate report fetcher will be initialized.
* `output` - output supported by [`garf-io` library](../garf_io/README.md).

///

/// tab | Python
```python
from garf_executors import api_executor
from garf_youtube_data_api import report_fetcher


fetcher = report_fetcher.YouTubeDataApiReportFetcher()

query_executor = api_executor.ApiQueryExecutor(fetcher)
context = api_executor.ApiExecutionContext(writer='csv')

query_text = """
SELECT
  id,
  snippet.publishedAt AS published_at,
  snippet.title AS title
FROM videos
"""

# execute query and save results to `campaign.csv`
query_executor.execute(query=query_text, title="campaign", context=context)
```
///

## Customization

If your report fetcher requires additional parameters you can pass them via key value pairs under `--source.` argument, i.e.`--source.regionCode='US'` - to get data only from *US*.
!!! note
    Concrete `--source` parameters are dependent on a particular report fetcher and should be looked up in a documentation for this fetcher.

### Macros




### Templates
