# garf for YouTube Data API

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
