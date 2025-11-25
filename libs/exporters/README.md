# garf exporter - Prometheus exporter for garf.

[![PyPI](https://img.shields.io/pypi/v/garf-exporter?logo=pypi&logoColor=white&style=flat-square)](https://pypi.org/project/garf-exporter)
[![Downloads PyPI](https://img.shields.io/pypi/dw/garf-exporter?logo=pypi)](https://pypi.org/project/garf-exporter/)

`garf-exporter` allows you to transform responses from APIs into metrics consumable for by Prometheus.
Simply define a config file with garf queries and run a single `garf-exporter` command to start exporting in no time!


## Installation


```bash
pip install garf-exporter
```

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

> To treat any field in SELECT statement as metric prefix with with `metric_`.

You need to explicitly specify source of API and path to config file to start exporting data.

```bash
garf-exporter --source API_SOURCE -c config.yaml
```

Once `garf-exporter` is running you can see exposed metrics at `localhost:8000/metrics`.

### Customization

* `--config` - path to `garf_exporter.yaml`, can be taken from local or remote file.
* `--expose-type` - type of exposition (`http` or `pushgateway`, `http` is used by default)
* `--host` - address of your http server (`localhost` by default)
* `--port` - port of your http server (`8000` by default)
* `--delay-minutes` - delay in minutes between scrapings (`15` by default)

## Documentation

Explore full documentation on using `garf-exporter`

* [Documentation](https://google.github.io/garf/usage/exporters/)
