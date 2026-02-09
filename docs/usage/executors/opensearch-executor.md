# OpenSearch Executor

OpenSearch executor allows you to execute SQL code over indexes in
[OpenSearch](https://docs.opensearch.org/latest/sql-and-ppl/sql/index/).

## Install

Ensure that `garf-executors` library is installed with OpenSearch support:

```
pip install garf-executors[opensearch]
```

## Usage

After `garf-executors` is installed you can use `garf` utility to perform fetching.

/// tab | bash
```bash
echo "SELECT campaign_id FROM opensearch_index" > query.sql

garf query.sql --source opensearch --output csv
```
where

* `query`- local or remote path(s) to files with queries.
* `output` - output supported by [`garf-io` library](https://google.github.io/garf/usage/writers/).
///

/// tab | Python

```python
from garf.executors.opensearch_executor import OpenSearchQueryExecutor
from opensearchpy import OpenSearch


client = OpenSearch(
    hosts = [{'host': 'localhost', 'port': 9200}],
    http_compress = True, # enables gzip compression for request bodies
    http_auth = ('admin', 'admin'),
    use_ssl = True,
    verify_certs = False,
    ssl_assert_hostname = False,
    ssl_show_warn = False
)

query_executor = OpenSearchQueryExecutor(client=client)

query_text = "SELECT campaign_id FROM opensearch_index"

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
  "source": "opensearch",
  "query": "SELECT campaign_id FROM opensearch_index",
  "title": "campaign",
  "context": {
    "writer": "csv"
  }
}'
```
///

## Parameters

### hosts

By default `garf` expects opensearch running on `localhost:9200`. You can adjust this
via `hosts` parameter (each host should be provided in `host:port` format).


/// tab | bash
```bash
echo "SELECT campaign_id FROM opensearch_index" > query.sql

garf query.sql --source opensearch \
  --output csv \
  --source.hosts=opensearch1:9200,opensearch2:9200
```
///

/// tab | Python

```python
from garf.executors.opensearch_executor import OpenSearchQueryExecutor

query_executor = OpenSearchQueryExecutor(
  hosts=['opensearch1:9200', 'opensearch2:9200']
)

query_text = "SELECT campaign_id FROM opensearch_index"

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
  "source": "opensearch",
  "query": "SELECT campaign_id FROM opensearch_index",
  "title": "campaign",
  "context": {
    "writer": "csv",
    "fetcher_parameters": {
      "hosts":  [
        "opensearch1:9200",
        "opensearch2:9200"
      ]
    }
  },
}'
```
///

### client

`OpenSearchQueryExecutor` can be customized with `opensearch-py` client.

/// tab | Python
```python hl_lines="15"
from garf.executors.opensearch_executor import OpenSearchQueryExecutor
from opensearchpy import OpenSearch


client = OpenSearch(
  hosts = [{'host': 'localhost', 'port': 9200}],
  http_compress = True,
  http_auth = ('admin', 'admin'),
  use_ssl = True,
  verify_certs = False,
  ssl_assert_hostname = False,
  ssl_show_warn = False
)

query_executor = OpenSearchQueryExecutor(client=client)
```
///
