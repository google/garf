# SQL Executor

SQL executor allows you to execute SQL code via any database
supported by [SqlAlchemy](https://docs.sqlalchemy.org/en/20/dialects/).

## Install

Ensure that `garf-executors` library is installed with SqlAlchemy support:

```
pip install garf-executors[sql]
```

## Usage

After `garf-executors` is installed you can use `garf` utility to perform fetching.

!!!important
    `sql` executor expects a `connection_string` parameter in
    [SqlAlchemy format](https://docs.sqlalchemy.org/en/20/core/engines.html).
    If it's not provided queries are executed via in-memory sqlite database.

/// tab | bash
```bash
echo "SELECT campaign_id FROM table" > query.sql

garf query.sql --source sqldb \
  --output csv
```
where

* `query`- local or remote path(s) to files with queries.
* `output` - output supported by [`garf-io` library](https://google.github.io/garf/usage/writers/).
///

/// tab | Python

```python
from garf.executors.sql_executor import SqlAlchemyQueryExecutor


query_executor = SqlAlchemyQueryExecutor()

query_text = "SELECT campaign_id FROM table"

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
  "source": "sqldb",
  "query": "SELECT campaign_id FROM table",
  "title": "campaign",
  "context": {
    "writer": "csv"
  }
}'
```
///

## Parameters

### connection_string

`SqlAlchemyQueryExecutor` requires connection string to the database.

/// tab | cli
```bash hl_lines="3"
garf query.sql --source sqldb \
  --output csv \
  --sqldb.connection_string=DB_CONNECTION_STRING
```
///

/// tab | Python
```python hl_lines="4"
from garf.executors.sql_executor import SqlAlchemyQueryExecutor

query_executor = (
  SqlAlchemyQueryExecutor.from_connection_string('DB_CONNECTION_STRING')
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
  "source": "sqldb",
  "query": "SELECT campaign_id FROM table",
  "title": "campaign",
  "context": {
    "writer": "csv",
    "fetcher_parameters": {
      "connection_string": "DB_CONNECTION_STRING"
    }
  }
}'
```
///
