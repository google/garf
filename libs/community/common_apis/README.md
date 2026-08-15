# `garf` for Common Public REST APIs

[![PyPI](https://img.shields.io/pypi/v/garf-common-apis?logo=pypi&logoColor=white&style=flat-square)](https://pypi.org/project/garf-common-apis)

`garf-common-apis` provides named `--source` aliases for popular public REST
APIs, built on top of the existing garf REST source.

## Why use this instead of `--source rest`?

garf's built-in `--source rest` already works with any HTTP API, including
OpenWeatherMap and CurrencyAPI.  These sources exist to remove the boilerplate:

| | `--source rest` | `--source openweather` / `--source currencyapi` |
|---|---|---|
| Endpoint URL | Must always pass `--source.endpoint=https://...` | Built in, override optional |
| Authentication | User must know the param name and put it in the query | Handled internally, never in query files |
| Response shape | User must know the JSON paths to select fields | Normalised automatically |

With `--source rest` you would write:
```sql
-- You must know the endpoint, inject appid in WHERE, and navigate nested JSON
SELECT main.temp, weather[0].description
FROM weather
WHERE lat={lat} AND lon={lon} AND appid={api_key}
```

With `--source openweather` you write:
```sql
-- Just the data you want
SELECT main.temp, weather[0].description AS conditions
FROM weather
WHERE lat={lat} AND lon={lon}
```

## Included sources

| Source | API | Docs |
|---|---|---|
| `openweather` | [OpenWeatherMap](https://openweathermap.org/api) | [openweathermap.org/appid](https://openweathermap.org/appid) |
| `currencyapi` | [CurrencyAPI](https://currencyapi.com) | [currencyapi.com/docs](https://currencyapi.com/docs) |

## Installation

```bash
pip install garf-common-apis
```

---

## OpenWeather (`--source openweather`)

Requires an [OpenWeatherMap API key](https://openweathermap.org/appid).

**What this source handles for you:**
- Injects the API key as the `appid` query parameter automatically
- Wraps OpenWeather's single-object JSON response into a list so garf parsers
  work normally
- Default endpoint: `https://api.openweathermap.org/data/2.5`

### CLI

```bash
garf current_weather.sql --source openweather \
  --source.api_key=YOUR_KEY \
  --macro.lat=33.44 \
  --macro.lon=-94.04 \
  --output csv
```

### Python

```python
from garf.community.common_apis.openweather import OpenWeatherApiReportFetcher
from garf.io import writer

fetcher = OpenWeatherApiReportFetcher(api_key='YOUR_KEY')

query = """
SELECT
  name AS city,
  main.temp AS temperature_kelvin,
  main.humidity AS humidity_pct,
  weather[0].description AS conditions,
  wind.speed AS wind_speed_ms
FROM weather
WHERE lat=33.44
  AND lon=-94.04
"""

report = fetcher.fetch(query)
writer.create_writer('csv').write(report, 'weather')
```

### Available source parameters

| Parameter | Description | Default |
|---|---|---|
| `api_key` | OpenWeatherMap API key (required) | — |
| `endpoint` | Override the base URL | `https://api.openweathermap.org/data/2.5` |

### Example queries

See [`examples/openweather/`](examples/openweather/):

- `current_weather.sql` — current conditions (temp, humidity, wind, …) for a lat/lon
- `forecast.sql` — 5-day / 3-hour forecast with precipitation probability

---

## CurrencyAPI (`--source currencyapi`)

Requires a [CurrencyAPI key](https://currencyapi.com/docs).

**What this source handles for you:**
- Sends the API key as the `apikey` HTTP header automatically — it never
  appears in URLs or query files
- Flattens the nested response structure so you can `SELECT code, value`
  directly without customizers:
  ```
  Raw:  {"data": {"USD": {"code": "USD", "value": 1.08}, "GBP": {...}}}
  Rows: [{"code": "USD", "value": 1.08}, {"code": "GBP", "value": 0.85}]
  ```
- Merges top-level metadata fields (e.g. `last_updated_at`) into each row
- Default endpoint: `https://api.currencyapi.com/v3`

### CLI

```bash
garf latest_rates.sql --source currencyapi \
  --source.api_key=YOUR_KEY \
  --macro.base_currency=EUR \
  --macro.currencies=USD,GBP,JPY \
  --output csv
```

### Python

```python
from garf.community.common_apis.currencyapi import CurrencyApiReportFetcher
from garf.io import writer

fetcher = CurrencyApiReportFetcher(api_key='YOUR_KEY')

query = """
SELECT
  code,
  value AS rate
FROM latest
WHERE base_currency=EUR
  AND currencies=USD,GBP,JPY
"""

report = fetcher.fetch(query)
writer.create_writer('csv').write(report, 'rates')
```

### Available source parameters

| Parameter | Description | Default |
|---|---|---|
| `api_key` | CurrencyAPI secret key (required) | — |
| `endpoint` | Override the base URL | `https://api.currencyapi.com/v3` |

### Example queries

See [`examples/currencyapi/`](examples/currencyapi/):

- `latest_rates.sql` — latest exchange rates for a given base currency
- `historical_rates.sql` — historical rates for a specific date
