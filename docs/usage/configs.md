# Configs

Config file captures all runtime parameters supplied to `garf`.
By using config you can use the same [queries](queries.md) and [workflows](workflows.md)
but provide different parameters for a particular run (i.e. prod/dev).


## Config Structure

Configs are defined in YAML files. The core structure consists of a two elements -
`sources` describing setup of a particular fetcher  and `global_parameters` applied to every
source in `sources`.

```yaml
sources:
  source-alias:
    writer: bq
    writer_parameters:
    fetcher_parameters:

global_parameters:
  query_parameters:
  fetcher_parameters:
  writer_parameters:

```

where:

*   **source-alias**: The source of data. Check [available fetchers](../fetchers/overview.md).
*   **fetcher_parameters**: Key value pairs used to fine-tune fetching process.
*   **writer**: Where the data should be saved. Check [available writers](writers.md).
*   **writer_parameters**: Key value pairs used to fine-tune writing process.
*   **query_parameters**: Parameters for dynamically changing query text.

## Usage

/// tab | cli
```bash
garf query.sql -c config.yaml
```

///

## Overwriting parameters


`garf` allows you to overwrite parameters specified in config; CLI args take
higher precedence than values in config.


For example, to display data in console instead of BigQuery, you can provide
a different writer as an argument.

/// tab | cli
```bash
garf query.sql -c config.yaml --writer console
```

///
