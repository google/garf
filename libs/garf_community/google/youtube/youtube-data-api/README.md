# `garf` for YouTube Data API

[![PyPI](https://img.shields.io/pypi/v/garf-youtube-data-api?logo=pypi&logoColor=white&style=flat-square)](https://pypi.org/project/garf-youtube-data-api)
[![Downloads PyPI](https://img.shields.io/pypi/dw/garf-youtube-data-api?logo=pypi)](https://pypi.org/project/garf-youtube-data-api/)

`garf-youtube-data-api` simplifies fetching data from YouTube Data API using SQL-like queries.

## Prerequisites

* [YouTube Data API](https://console.cloud.google.com/apis/library/youtube.googleapis.com) enabled.
* [API key](https://support.google.com/googleapi/answer/6158862?hl=en) to access to access YouTube Data API.
    > Once generated expose API key as `export GARF_YOUTUBE_DATA_API_KEY=<YOUR_API_KEY>`

## Installation

`pip install garf-youtube-data-api`

## Usage

### Run as a library
```
from garf_youtube_data_api import report_fetcher
from garf_io import writer


# Specify query
query = 'SELECT id, snippet.title AS channel_name FROM channels'

# Fetch report
fetched_report = (
  report_fetcher.YouTubeDataApiReportFetcher()
  .fetch(query, id=[<YOUR_CHANNEL_ID_HERE>])
)

# Write report to console
console_writer = writer.create_writer('console')
console_writer.write(fetched_report, 'output')
```

### Run via CLI

> Install `garf-executors` package to run queries via CLI (`pip install garf-executors`).

```
garf <PATH_TO_QUERIES> --source youtube-data-api \
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
| `id`   | id of YouTube channel or videos| Multiple ids are supported, should be comma-separated|
| `forHandle` | YouTube channel handle | i.e. @myChannel |
| `forUsername` | YouTube channel name | i.e. myChannel |
| `regionCode` | ISO 3166-1 alpha-2 country code | i.e. US |
| `chart` | `mostPopular` | Gets most popular in `regionCode`, can be narrowed down with `videoCategoriId` |
