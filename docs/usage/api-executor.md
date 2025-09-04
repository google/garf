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


garf query.sql --source youtube_data_api \
  --output console \
  --source.ids=VIDEO_ID
```

where

* `query` - local or remote path(s) to files with queries.
* `source`- type of API to use. Based on that the appropriate report fetcher will be initialized.
* `output` - output supported by [`garf-io` library](https://google.github.io/garf/usage/writers/).

///
/// tab | Python
```python
from garf_executors import api_executor



query_executor = api_executor.ApiQueryExecutor.from_fetcher_alias(
  'youtube-data-api'
)
context = api_executor.ApiExecutionContext(writer='csv')

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
