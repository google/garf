# garf exporter - Prometheus exporter for garf.

[![PyPI](https://img.shields.io/pypi/v/garf-exporter?logo=pypi&logoColor=white&style=flat-square)](https://pypi.org/project/garf-exporter)
[![Downloads PyPI](https://img.shields.io/pypi/dw/garf-exporter?logo=pypi)](https://pypi.org/project/garf-exporter/)


## Installation and usage

### Locally

1. Install `garf-exporter` from pip:

```
pip install garf-exporter
```
2. Run `garf-exporter`:

```
garf-exporter
```

### Docker

```
docker run --network=host \
  -v `pwd`/garf_exporter.yaml:/app/garf_exporter.yaml \
  garf_exporter
```

```
docker run --network=host garf_exporter \
  --config gs://path/to/garf_config.yaml

```
By default it will start http_server on `localhost:8000` and will push some basic metrics to it.

### Customization

* `--config` - path to `garf_exporter.yaml`
  >  `config` can be taken from local storage or remote storage.
* `--expose-type` - type of exposition (`http` or `pushgateway`, `http` is used by default)
* `--host` - address of your http server (`localhost` by default)
* `--port` - port of your http server (`8000` by default)
* `--delay-minutes` - delay in minutes between scrapings (`15` by default)


### Customizing fetching dates

By default `garf-exporter` fetches performance data for TODAY; if you want to
customize it you can provide optional flags:
* `--macro.start_date=:YYYYMMDD-N`, where `N` is number of days starting from today
* `--macro.end_date=:YYYYMMDD-M`, where `N` is number of days starting from today

It will add an additional metric to be exposed to Prometheus `*_n_days` (i.e.
`googleads_clicks_n_days`).
