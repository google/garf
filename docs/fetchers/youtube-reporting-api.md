# garf for YouTube Data API

[![PyPI](https://img.shields.io/pypi/v/garf-youtube-reporting-api?logo=pypi&logoColor=white&style=flat-square)](https://pypi.org/project/garf-youtube-reporting-api)
[![Downloads PyPI](https://img.shields.io/pypi/dw/garf-youtube-reporting-api?logo=pypi)](https://pypi.org/project/garf-youtube-reporting-api/)

## Install

Install `garf-youtube-reporting-api` library

/// tab | pip
```
pip install garf-executors garf-youtube-reporting-api
```
///

/// tab | uv
```
uv pip install garf-executors garf-youtube-reporting-api
```
///

## Usage

```
garf <PATH_TO_QUERIES> --source youtube-reporting-api \
  --output csv \
  --source.id=YOUTUBE_CHANNEL_ID
```

where:

* `query` - local or remote path(s) to files with queries.
* `output` - output supported by [`garf-io` library](https://google.github.io/garf/usage/writers/).

###  Available source parameters

| name | values| comments |
|----- | ----- | -------- |
| `id`   | id of YouTube channel or videos| Multiple ids are supported, should be comma-separated|
| `forHandle` | YouTube channel handle | i.e. @myChannel |
| `forUsername` | YouTube channel name | i.e. myChannel |
| `regionCode` | ISO 3166-1 alpha-2 country code | i.e. US |
| `chart` | `mostPopular` | Gets most popular in `regionCode`, can be narrowed down with `videoCategoriId` |
