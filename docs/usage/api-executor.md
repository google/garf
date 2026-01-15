#ApiExecutor

If your job is to execute query and write it to local/remote storage you can use `ApiQueryExecutor` to do it easily.

## Install

Ensure that `garf-executors` library is installed:

```bash
pip install garf-executors
```
## Run

Let's take an example of working with [YouTube Data API fetcher](../fetchers/youtube-data-api.md) to get some stats on YouTube video.

!!! important
    Make sure that corresponding library for interacting with YouTube Data API is installed

    ```bash
    pip install garf_youtube_data_api
    ```

/// tab | bash

```bash

echo "
SELECT
  id,
  snippet.publishedAt AS published_at,
  snippet.title AS title
FROM videos" > query.sql


garf query.sql --source youtube-data-api \
  --output csv \
  --source.ids=VIDEO_ID
```

where

* `query` - local or remote path(s) to files with queries.
* `source`- type of API to use. Based on that the appropriate report fetcher will be initialized.
* `output` - output supported by [`garf-io` library](https://google.github.io/garf/usage/writers/).

///
/// tab | Python
```python
from garf.executors import setup_executor


query_executor = setup_executor(source='youtube-data-api')
context = api_executor.ApiExecutionContext(
  writer='csv',
  fetcher_parameters={'id': 'VIDEO_ID'}
)

query_text = """
SELECT
  id,
  snippet.publishedAt AS published_at,
  snippet.title AS title
FROM videos
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
  "source": "youtube-data-api",
  "query": "SELECT id, snippet.publishedAt AS published_at, snippet.title AS title FROM videos",
  "title": "query",
  "context": {
    "writer": "csv",
    "fetcher_parameters": {
      "id": "VIDEO_ID"
    }
  }
}'
```
///


### Caching

When running queries you can get data from cache rather that fetching them from API.


Cache has `cache_ttl_seconds` parameter (default is 3600 seconds or 1 hour).


/// tab | bash

```
garf query.sql --source youtube_data_api \
  --output console \
  --source.id=VIDEO_ID \
  --enable-cache \
  --cache-ttl-seconds 300
```
///

/// tab | Python
```python
from garf.executors import setup_executor


query_executor = setup_executor(
  source='youtube-data-api',
  enable_cache=True,
  cache_ttl_seconds=300
)
context = api_executor.ApiExecutionContext(
  writer='csv',
  fetcher_parameters={'id': 'VIDEO_ID'}
)

query_text = """
SELECT
  id,
  snippet.publishedAt AS published_at,
  snippet.title AS title
FROM videos
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
  "source": "youtube-data-api",
  "query": "SELECT id, snippet.publishedAt AS published_at, snippet.title AS title FROM videos",
  "title": "query",
  "context": {
    "fetcher_parameters": {
      "id": "VIDEO_ID",
      "enable_cache": True,
      "cache_ttl_seconds': 300
    }
  }
}'
```
///
