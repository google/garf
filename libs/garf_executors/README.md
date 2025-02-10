# `garf-executors` - One stop-shop for interacting with Reporting APIs.

`garf-executors` is responsible for orchestrating process of fetching from API and storing data in a storage.

Currently the following executors are supports:

* `ApiExecutor` - fetching data from reporting API and saves it to a requested destination.
* `BigQueryExecutor` - executes SQL code in BigQuery.
* `SqlExecutor` - executes SQL code in a SqlAlchemy supported DB.

## Installation

`pip install garf-executors`

## Usage

After `garf-executors` is installed you can use `garf` utility to perform fetching.

```
garf <QUERIES> --source <API_SOURCE> \
  --output <OUTPUT_TYPE> \
  --source.params1=<VALUE>
```

where

* `<QUERIES>`- local or remote path(s) to files with queries.
* `<API_SOURCE>`- type of API to use. Based on that the appropriate report fetcher will be initialized.
* `<OUTPUT_TYPE>` - output supported by [`garf-io` library](../garf_io/README.md).

If your report fetcher requires additional parameters you can pass them via key value pairs under `--source.` argument, i.e.`--source.regionCode='US'` - to get data only from *US*.
> Concrete `--source` parameters are dependent on a particular report fetcher and should be looked up in a documentation for this fetcher.
