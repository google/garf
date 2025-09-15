# SQL Executor

## Install

Ensure that `garf-executors` library is installed with SqlAlchemy support:

```
pip install garf-executors[sql]
```

## Usage

After `garf-executors` is installed you can use `garf` utility to perform fetching.

/// tab | bash
```
garf <QUERIES> --source sqldb \
  --output <OUTPUT_TYPE> \
  --source.connection_string=DB_CONNECTION_STRING
```
where

* `query`- local or remote path(s) to files with queries.
* `output` - output supported by [`garf-io` library](https://google.github.io/garf/usage/writers/).
///

/// tab | Python

```python
from garf_executors.sql_executor import SqlAlchemyQueryExecutor


query_executor = (
  SqlAlchemyQueryExecutor.from_connection_string(connection_string)
)

query_text = "SELECT campaign.id AS campaign_id FROM table"

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
