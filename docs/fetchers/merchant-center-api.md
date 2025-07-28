# garf for Merchant Center API

## Install

Install `garf-merchant-api` library

```
pip install garf-executors garf-merchant-api
```

## Usage

```
garf <PATH_TO_QUERIES> --source merchant-api \
  --output <OUTPUT_TYPE> \
  --source.<SOURCE_PARAMETER=VALUE>
```

where:

* `<PATH_TO_QUERIES>` - local or remove files containing queries
* `<OUTPUT_TYPE>` - output supported by [`garf-io` library](../garf_io/README.md).
* `<SOURCE_PARAMETER=VALUE` - key-value pairs to refine fetching, check [available source parameters](#available-source-parameters).

### Available source parameters

| name | values| comments |
|----- | ----- | -------- |
| `account`   | Account(s) to get data to | Multiple accounts are supported, should be comma-separated|
