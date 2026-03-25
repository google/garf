# Overview

[![PyPI](https://img.shields.io/pypi/v/garf-executors?logo=pypi&logoColor=white&style=flat-square)](https://pypi.org/project/garf-executors)
[![Downloads PyPI](https://img.shields.io/pypi/dw/garf-executors?logo=pypi)](https://pypi.org/project/garf-executors/)

`garf-executors` is responsible for orchestrating process of fetching from API and storing data in a storage.

Currently the following executors are supported:

* [`ApiExecutor`](executors/api-executor.md) - fetches data from reporting API and saves it to a requested destination.
* [`BigQueryExecutor`](executors/bq-executor.md) - executes SQL code in BigQuery.
* [`SqlExecutor`](executors/sql-executor.md) - executes SQL code in a SqlAlchemy supported DB.
* [`DuckDBExecutor`](executors/duckdb-executor.md) - executes SQL code over various files formats
supported by [DuckDB](https://duckdb.org/docs/stable/data/data_sources).
* [`OpenSearchExecutor`](executors/opensearch-executor.md) - executes SQL code over indexes in
[OpenSearch](https://docs.opensearch.org/latest/sql-and-ppl/sql/index/).

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

/// tab | server
```bash
pip install garf-executors[server]
```
///

## Usage

After `garf-executors` is installed you can use `garf` utility to perform fetching.

/// tab | cli
```bash
garf <QUERIES> --source <API_SOURCE> \
  --output <OUTPUT_TYPE>
```

where

* `query` - local or remote path(s) to files with queries.
* `source`- type of API to use. Based on that the appropriate report fetcher will be initialized.
* `output` - output supported by [`garf-io` library](https://google.github.io/garf/usage/writers/).

///

/// tab | Python
```python
from garf.executors import api_executor


query_executor = (
  api_executor.ApiQueryExecutor.from_fetcher_alias(
    source='API_SOURCE',
)
context = api_executor.ApiExecutionContext(writer='OUTPUT_TYPE')

query_text = 'YOUR_QUERY_HERE'

query_executor.execute(
  query=query_text,
  title="query",
  context=context
)
```

!!!note
    You can use `aexecute` method to run execute the query asynchronously
    ```python
    await query_executor.aexecute(
      query=query_text,
      title="query",
      context=context
    )
    ```

///

/// tab | server

!!!note
    Ensure that API endpoint for `garf` is running.
    ```bash
    python -m garf.executors.entrypoints.server
    ```

```bash
curl -X 'POST' \
  'http://127.0.0.1:8000/api/execute' \
  -H 'accept: application/json' \
  -H 'Content-Type: application/json' \
  -d '{
  "source": "API_SOURCE",
  "title": "query",
  "query": "YOUR_QUERY_HERE",
  "context": {
    "writer": "OUTPUT_TYPE"
  }
}'
```
///

## Customization

### Source

If your report fetcher requires additional parameters (accounts, ids, regions, categories, etc.) you can easily provide them.
!!! note
    Concrete `--source` parameters are dependent on a particular report fetcher and should be looked up in a documentation for this fetcher.

/// tab | cli
```bash
garf <QUERIES> --source <API_SOURCE> \
  --output <OUTPUT_TYPE> \
  --source.params1=<VALUE>
```

where

* `query` - local or remote path(s) to files with queries.
* `source`- type of API to use. Based on that the appropriate report fetcher will be initialized.
* `output` - output supported by [`garf-io` library](https://google.github.io/garf/usage/writers/).

///

/// tab | Python
```python
from garf.executors import api_executor


query_executor = (
  api_executor.ApiQueryExecutor.from_fetcher_alias(
    source='API_SOURCE',
)
context = api_executor.ApiExecutionContext(
  writer='OUTPUT_TYPE',
  fetcher_parameters={
    'param1': 'VALUE',
  }
)

query_text = 'YOUR_QUERY_HERE'

query_executor.execute(
  query=query_text,
  title="query",
  context=context
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
  "source": "API_SOURCE",
  "title": "query",
  "query": "YOUR_QUERY_HERE",
  "context": {
    "writer": "OUTPUT_TYPE",
    "fetcher_parameters": {
      "param1": "VALUE"
    }
  }
}'
```
///


### Macro

If your query contains [macros](https://google.github.io/garf/usage/queries/#macros) you can provide values for them.
Macros will be substituted by any value provided.

/// tab | cli
```bash
echo 'SELECT {key} AS value FROM resource' > query.sql

garf query.sql --source <API_SOURCE> \
  --output <OUTPUT_TYPE> \
  --macro.key=VALUE
```
///

/// tab | Python
```python
from garf.executors import api_executor


query_executor = (
  api_executor.ApiQueryExecutor.from_fetcher_alias(
    source='API_SOURCE',
)
context = api_executor.ApiExecutionContext(
  writer='OUTPUT_TYPE',
  query_parameters={
    'query_parameters': {
      'macro': {
        'key': 'VALUE',
      }
    }
  }
)

query_text = 'SELECT {key} AS value FROM resource'

query_executor.execute(
  query=query_text,
  title="query",
  context=context
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
  "source": "API_SOURCE",
  "title": "query",
  "query": "SELECT {key} AS value FROM resource",
  "context": {
    "writer": "OUTPUT_TYPE",
    "query_parameters": {
      "macro":  {
        "key": "VALUE"
      }
    }
  }
}'
```
///


### Template

If your query contains [templates](https://google.github.io/garf/usage/queries/#templates) you can provide values for them.
Template will be dynamically change the query based on provided inputs.

/// tab | cli
```bash
echo """
SELECT
  {% if key == '0' %}
  column_1
  {% else %}
  column_2
  {% endif %}
FROM resource
""" > query.sql

garf query.sql --source <API_SOURCE> \
  --output <OUTPUT_TYPE> \
  --template.key=VALUE
```
///

/// tab | Python
```python
from garf.executors import api_executor


query_executor = (
  api_executor.ApiQueryExecutor.from_fetcher_alias(
    source='API_SOURCE',
)
context = api_executor.ApiExecutionContext(
  writer='OUTPUT_TYPE',
  query_parameters={
    'query_parameters': {
      'template': {
        'key': 'VALUE',
      }
    }
  }
)

query_text = """
SELECT
  {% if key == '0' %}
  column_1
  {% else %}
  column_2
  {% endif %}
FROM resource
"""

query_executor.execute(
  query=query_text,
  title="query",
  context=context
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
  "source": "API_SOURCE",
  "title": "query",
  "query": "SELECT {% if key == '0' %} column_1 {% else %} column_2 {% endif %} FROM resource",
  "context": {
    "writer": "OUTPUT_TYPE",
    "query_parameters": {
      "template":  {
        "key": "VALUE"
      }
    }
  }
}'
```
///


## gQuery expansion

`garf` allows you to call itself to dynamically provide parameters for macro,
template, or source using `gquery` prefix.

The structure of `gquery` is follows:

```
gquery:source_alias:select_statement
```

where:

* `source_alias` is an alias for a source (currently only `bq` and `sqldb`
are supported).
* `select_statement` - valid SQL statement that should return **a single column**.

For example, if your query hash `ids` macro and you want to dynamically provide
them based on some table in BigQuery, you can include use the following `gquery`
as a macro.

/// tab | cli
```bash hl_lines="6"
echo 'SELECT {key} AS value FROM resource WHERE id IN ({ids})' > query.sql

garf query.sql --source <API_SOURCE> \
  --output <OUTPUT_TYPE> \
  --macro.key=VALUE \
  --macro.ids=gquery:bq:SELECT id FROM my_dataset.my_table
```
///

/// tab | Python
```python hl_lines="14"
from garf.executors import api_executor


query_executor = (
  api_executor.ApiQueryExecutor.from_fetcher_alias(
    source='API_SOURCE',
)
context = api_executor.ApiExecutionContext(
  writer='OUTPUT_TYPE',
  query_parameters={
    'query_parameters': {
      'macro': {
        'key': 'VALUE',
        'ids': 'gquery:bq:SELECT id FROM my_dataset.my_table',
      }
    }
  }
)

query_text = 'SELECT {key} AS value FROM resource WHERE id IN ({ids})'

query_executor.execute(
  query=query_text,
  title="query",
  context=context
)
```
///

/// tab | server
```bash hl_lines="14"
curl -X 'POST' \
  'http://127.0.0.1:8000/api/execute' \
  -H 'accept: application/json' \
  -H 'Content-Type: application/json' \
  -d '{
  "source": "API_SOURCE",
  "title": "query",
  "query": "SELECT {key} AS value FROM resource WHERE id IN ({ids})",
  "context": {
    "writer": "OUTPUT_TYPE",
    "query_parameters": {
      "macro":  {
        "key": "VALUE",
        "ids": "gquery:bq:SELECT id FROM my_dataset.my_table"
      }
    }
  }
}'
```
///

!!!note
    If your `gquery` contains macros and templates you need to explicitly
    provide them as `macro` or `template` parameter.

    ```bash hl_lines="6"
    echo 'SELECT {key} AS value FROM resource WHERE id IN ({ids})' > query.sql

    garf query.sql --source <API_SOURCE> \
      --output <OUTPUT_TYPE> \
      --macro.key=VALUE \
      --macro.dataset=my_dataset \
      --macro.ids=gquery:bq:SELECT id FROM {dataset}.my_table
    ```

### Setting up executor for gquery

Depending on setup you might need to configure `bq` or `sqldb` executor.

```bash hl_lines="6"
echo 'SELECT {key} AS value FROM resource WHERE id IN ({ids})' > query.sql

garf query.sql --source <API_SOURCE> \
  --output <OUTPUT_TYPE> \
  --macro.key=VALUE \
  --bq.project=my-bq-project \
  --macro.dataset=my_dataset \
  --macro.ids=gquery:bq:SELECT id FROM {dataset}.my_table
```




## Batch execution

You can to execute multiple queries in parallel.


/// tab | cli
```bash
garf *.sql --source <API_SOURCE> \
  --output <OUTPUT_TYPE> \
  --parallel-threshold 10
```
///

/// tab | Python
```python
from garf.executors import api_executor


query_executor = (
  api_executor.ApiQueryExecutor.from_fetcher_alias(
    source='API_SOURCE',
)
context = api_executor.ApiExecutionContext(
  writer='OUTPUT_TYPE',
)

query_text_1 = "SELECT column FROM resource1"
query_text_2 = "SELECT column FROM resource2"
batch = {
  'query_1': query_text_1,
  'query_2': query_text_2,
}

query_executor.execute_batch(
  batch=batch,
  context=context,
  parallel_threshold=10,
)
```
///

/// tab | server
```bash
curl -X 'POST' \
  'http://127.0.0.1:8000/api/execute:batch' \
  -H 'accept: application/json' \
  -H 'Content-Type: application/json' \
  -d '{
  "source": "API_SOURCE",
  "query_path": [
    "path/to/query1.sql",
    "path/to/query2.sql"
  ],
  "context": {
    "writer": "OUTPUT_TYPE"
  }
}'
```
///
