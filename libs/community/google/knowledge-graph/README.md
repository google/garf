# `garf` for Knowledge Graph Search API

[![PyPI](https://img.shields.io/pypi/v/garf-knowledge-graph-api?logo=pypi&logoColor=white&style=flat-square)](https://pypi.org/project/garf-knowledge-graph-api)
[![Downloads PyPI](https://img.shields.io/pypi/dw/garf-knowledge-graph-api?logo=pypi)](https://pypi.org/project/garf-knowledge-graph-api/)

`garf-knowledge-graph-api` simplifies fetching data from Knowledge Graph Search API using SQL-like queries.

## Prerequisites

* [Knowledge Graph Search API](https://console.cloud.google.com/apis/library/kgsearch.googleapis.com) enabled.
* [API key](https://support.google.com/googleapi/answer/6158862?hl=en) to access to access Knowledge Graph Search API.
    > Once generated expose API key as `export KG_API_KEY=<YOUR_API_KEY>`

## Installation

`pip install garf-knowledge-graph-api`

## Usage

### Run as a library
```
from garf.community.google.knowledge_graph import report_fetcher
from garf.io import writer


# Specify query
query = """
  SELECT
    result_score,
    @id AS id,
    @type AS type,
    description,
    image.url AS url
  FROM query
  WHERE {query}
""

# Fetch report
fetched_report = (
  report_fetcher.KnowledgeGraphApiReportFetcher()
  .fetch(query, query="<YOUR_SEARCH_QUERY_HERE">)
)

# Write report to console
console_writer = writer.create_writer('console')
console_writer.write(fetched_report, 'output')
```

### Run via CLI

> Install `garf-executors` package to run queries via CLI (`pip install garf-executors`).

```
garf <PATH_TO_QUERIES> --source knowledge-graph-api \
  --output <OUTPUT_TYPE> \
  --source.<SOURCE_PARAMETER=VALUE>
```

where:

* `<PATH_TO_QUERIES>` - local or remove files containing queries
* `<OUTPUT_TYPE>` - output supported by [`garf-io` library](../garf_io/README.md).
* `<SOURCE_PARAMETER=VALUE` - key-value pairs to refine fetching, check [available source parameters](#available-source-parameters).

## Available source parameters

| name | values| comments |
|----- | ----- | -------- |
| `ids`   | One or many Knowledge Graph Ids | Multiple ids are supported, should be comma-separated|
| `query` | Search query | i.e. "Radiohead" |
