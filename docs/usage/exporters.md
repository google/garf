# garf exporter - Prometheus exporter for garf.

[![PyPI](https://img.shields.io/pypi/v/garf-exporter?logo=pypi&logoColor=white&style=flat-square)](https://pypi.org/project/garf-exporter)
[![Downloads PyPI](https://img.shields.io/pypi/dw/garf-exporter?logo=pypi)](https://pypi.org/project/garf-exporter/)

`garf-exporter` is responsible exposing garf-extracted data to Prometheus.

## Installation


/// tab | pip
```bash
pip install garf-exporter
```
///

/// tab |  uv
```bash
uv pip install garf-exporter
```
///

## Usage

`garf-exporter` expects a configuration file that contains garf-queries mapped to collector names.

Config file may contains one or several queries.

```yaml
- title: test
  query: |
    SELECT
      dimension,
      metric,
      metric_clicks,
      campaign
    FROM resource
```
!!!important
    To treat any field in SELECT statement as metric prefix with with `metric_`.

You need to explicitly specify source of API and path to config file to start exporting data.

```bash
garf-exporter --source API_SOURCE -c config.yaml
```

Once `garf-exporter` is running you can see exposed metrics at `localhost:8000/metrics`.

### Customization

#### Exporter

* `--config` - path to `garf_exporter.yaml`, can be taken from local or remote file.
* `--expose-type` - type of exposition (`http` or `pushgateway`, `http` is used by default)
* `--host` - address of your http server (`localhost` by default)
* `--port` - port of your http server (`8000` by default)
* `--delay-minutes` - delay in minutes between scrapings (`15` by default)

#### Source

Depending on a source selected you may need to provide source-specific parameters
in `--source.key=value` format (i.e. `--source.credentials_file=/app/credentials.json`).

#### Macro

If queries contain [macros](queries.md#macros) you need provide them
in `--macros.key=value` format (i.e. `--macro.start-date=20250101`).


## Examples

### Bid Manager API

1. Ensure that Bid Manager access is [configured](../fetchers/bid-manager.md#prerequisites).

1. Specify config

```yaml
- title: performance
  query: |
    SELECT
      advertiser,
      metric_clicks
    FROM standard
    WHERE advertiser = {advertiser}
      AND dataRange = CURRENT_DAY
  suffix: "Remove"
```

1. Start exporting

```bash
garf-exporter \
  --source bid-manager \
  -c config.yaml \
  --macro.advertiser=ADVERTISER_ID
```
