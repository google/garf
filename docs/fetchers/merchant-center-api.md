# garf for Merchant Center API

[![PyPI](https://img.shields.io/pypi/v/garf-merchant-api?logo=pypi&logoColor=white&style=flat-square)](https://pypi.org/project/garf-merchant-api)
[![Downloads PyPI](https://img.shields.io/pypi/dw/garf-merchant-api?logo=pypi)](https://pypi.org/project/garf-merchant-api/)

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
* `output` - output supported by [`garf-io` library](https://google.github.io/garf/usage/writers/).
* `<SOURCE_PARAMETER=VALUE` - key-value pairs to refine fetching, check [available source parameters](#available-source-parameters).

### Available source parameters

| name | values| comments |
|----- | ----- | -------- |
| `account`   | Account(s) to get data to | Multiple accounts are supported, should be comma-separated|
