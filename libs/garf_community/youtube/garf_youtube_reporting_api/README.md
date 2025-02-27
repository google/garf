# `garf` for YouTube Reporting API

[![PyPI](https://img.shields.io/pypi/v/garf-youtube-reporting-api?logo=pypi&logoColor=white&style=flat-square)](https://pypi.org/project/garf-youtube-reporting-api)
[![Downloads PyPI](https://img.shields.io/pypi/dw/garf-youtube-reporting-api?logo=pypi)](https://pypi.org/project/garf-youtube-reporting-api/)

`garf-youtube-reporting-api` simplifies fetching data from YouTube Reporting API using [SQL-like queries](../../../garf_core/docs/how-to-write-queries.md).

## Prerequisites

* [YouTube Reporting API](https://console.cloud.google.com/apis/library/youtubereporting.googleapis.com) enabled.
* [Client ID, client secret](https://support.google.com/cloud/answer/6158849?hl=en) and refresh token generated. \
> Please note you'll need to use another OAuth2 credentials type - *Web application*, and set "https://developers.google.com/oauthplayground" as redirect url in it.
* Refresh token. You can use [OAuth Playground](https://developers.google.com/oauthplayground/) to generate refresh token.
    * Select `https://www.googleapis.com/auth/yt-analytics.readonly` scope
    * Enter OAuth Client ID and OAuth Client secret under *Use your own OAuth credentials*;
    * Click on *Authorize APIs*

* Expose client id,  client secret and refresh token as environmental variables:
```
export YT_CLIENT_ID=
export YT_CLIENT_SECRET=
export YT_REFRESH_TOKEN=
```

## Installation

`pip install garf-youtube-reporting-api`

## Usage

### Run as a library
```
from garf_youtube_data_api import report_fetcher
from garf_io import writer


# Specify query
query = """
  SELECT
    dimensions.day AS date,
    metrics.views AS views
  FROM channel
  WHERE
    channel==MINE
    AND startDate = 2010-01-01
    AND endDate = 2024-01-01
  """

# Fetch report
fetched_report = report_fetcher.YouTubeReportingApiReportFetcher().fetch(query)

# Write report to console
console_writer = writer.create_writer('console')
console_writer.write(fetched_report, 'output')
```

### Run via CLI

> Install `garf-executors` package to run queries via CLI (`pip install garf-executors`).

```
garf <PATH_TO_QUERIES> --source youtube-reporting-api \
  --output <OUTPUT_TYPE> \
```

where:

* `<PATH_TO_QUERIES>` - local or remove files containing queries
* `<OUTPUT_TYPE>` - output supported by [`garf-io` library](../garf_io/README.md).
