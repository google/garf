# DuckDB Executor

DuckDB executor allows you to execute SQL code over various files formats
supported by [DuckDB](https://duckdb.org/docs/stable/data/data_sources).

## Install

Ensure that `garf-executors` library is installed with DuckDB support:

```
pip install garf-executors[duckdb]
```

## Usage

After `garf-executors` is installed you can use `garf` utility to perform fetching.

/// tab | bash
```bash
echo "SELECT campaign_id FROM 'data.csv'" > query.sql

garf query.sql --source duckdb --output csv
```
where

* `query`- local or remote path(s) to files with queries.
* `output` - output supported by [`garf-io` library](https://google.github.io/garf/usage/writers/).
///

/// tab | Python

```python
from garf.executors.duckdb_executor import DuckDBExecutor


query_executor = DuckDBExecutor()

query_text = "SELECT campaign_id FROM 'data.csv'"

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

/// tab | server

```bash
curl -X 'POST' \
  'http://127.0.0.1:8000/api/execute' \
  -H 'accept: application/json' \
  -H 'Content-Type: application/json' \
  -d '{
  "source": "duckdb",
  "query": "SELECT campaign_id FROM \"data.csv\"",
  "title": "campaign",
  "context": {
    "writer": "csv"
  }
}'
```
///
