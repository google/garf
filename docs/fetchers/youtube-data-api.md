# garf for YouTube Data API

## Install

Install `garf-youtube-data-api` library

```
pip install garf-executors garf-youtube-data-api
```

## Usage

```
garf <PATH_TO_QUERIES> --source youtube-data-api \
  --output <OUTPUT_TYPE> \
  --source.<SOURCE_PARAMETER=VALUE>
```

where:

* `<PATH_TO_QUERIES>` - local or remove files containing queries
* `<OUTPUT_TYPE>` - output supported by [`garf-io` library](../garf_io/README.md).
* `<SOURCE_PARAMETER=VALUE` - key-value pairs to refine fetching, check [available source parameters](#available-source-parameters).

###  Available source parameters

| name | values| comments |
|----- | ----- | -------- |
| `id`   | id of YouTube channel or videos| Multiple ids are supported, should be comma-separated|
| `forHandle` | YouTube channel handle | i.e. @myChannel |
| `forUsername` | YouTube channel name | i.e. myChannel |
| `regionCode` | ISO 3166-1 alpha-2 country code | i.e. US |
| `chart` | `mostPopular` | Gets most popular in `regionCode`, can be narrowed down with `videoCategoriId` |
