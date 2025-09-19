# Use garf as CLI tool

## Installation

```
pip install garf-executors
```

## Usage

After `garf-executors` is installed you can use `garf` utility to perform fetching.

```bash
garf <QUERIES> --source <API_SOURCE> \
  --output <OUTPUT_TYPE> \
  --source.params1=<VALUE>
```

where

* `query` - local or remote path(s) to files with queries.
* `source`- type of API to use. Based on that the appropriate report fetcher will be initialized.
* `output` - output supported by [`garf-io` library](https://google.github.io/garf/usage/writers/).

If your report fetcher requires additional parameters you can pass them via key value pairs under `--source.` argument, i.e.`--source.regionCode='US'` - to get data only from *US*.
> Concrete `--source` parameters are dependent on a particular report fetcher and should be looked up in a documentation for this fetcher.
