# Combine fetching and saving with `ApiQueryExecutor`

## Install

Ensure that `garf-executors` library is installed:

```
pip install garf-executors
```

## Initialize

If your job is to execute query and write it to local/remote storage you can use `ApiQueryExecutor` to do it easily.
> When reading query from file `ApiQueryExecutor` will use query file name as a name for output file/table.
/// tab | Python
```python
from garf_core.fetchers import FakeApiReportFetcher
from garf_executors import api_executor
from garf_io import reader


# initialize query_executor to fetch report and store them in local/remote storage
fake_report_fetcher = FakeApiReportFetcher(data=[{'campaign': {'id': 1}}])

query_executor = api_executor.ApiQueryExecutor(fetcher=fake_report_fetcher)

context = api_executor.ApiExecutionContext(writer='csv')
```
///

## Run

/// tab | bash

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

///
/// tab | Python
```python
query_text = "SELECT campaign.id AS campaign_id, FROM campaign"

# execute query and save results to `campaign.csv`
query_executor.execute(query=query_text, title="campaign", context=context)

# execute query from file and save to results to `query.csv`
reader_client = reader.FileReader()
query_path="path/to/query.sql"

query_executor.execute(
    query=reader_client.read(query_path),
    title=query_path,
    context=context
)
```
///
