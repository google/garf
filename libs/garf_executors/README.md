# `garf-executors` - One stop-shop for interacting with Reporting APIs.

`garf-executors` is responsible for orchestrating process of fetching from API and storing data in a storage.

Currently the following executors are supports:

* `ApiExecutor` - fetching data from reporting API and saves it to a requested destination.
* `BigQueryExecutor` - executes SQL code in BigQuery.
* `SqlExecutor` - executes SQL code in a SqlAlchemy supported DB.
