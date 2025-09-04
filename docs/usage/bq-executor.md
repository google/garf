# BigQuery Executor

`BigQueryExecutor` allows you to execute SQL code in BigQuery.

## Install

Ensure that `garf-executors` library is installed with BigQuery support:

```bash
pip install garf-executors[bq]
```

## Usage

After `garf-executors` is installed you can use `garf` utility to perform fetching.

/// tab | bash
```bash
garf <QUERIES> --source bq \
  --output csv \
  --source.project_id=MY_PROJECT
```
where

* `query`- local or remote path(s) to files with queries.
* `output` - output supported by [`garf-io` library](../garf_io/README.md).
///

/// tab | Python

```python
from garf_executors.bq_executor import BigQueryExecutor


query_executor = BigQueryExecutor(project_id=MY_PROJECT)

query_text = "SELECT campaign.id AS campaign_id FROM project.dataset.table"

# execute query and get report back
report = query_executor.execute(query=query_text, title="campaign")

# execute query and save results to `campaign.csv`
query_executor.execute(
  query=query_text,
  title="campaign",
  context={'writer': 'csv'}
)
```
///
