`garf` comes with built-in REST API support.


Currently `rest` fetcher are support working with APIs that have either
API key authentication or not authentication at all.

Depending on how a particular API provided expects you to provided an API key
in request - it can be either [included in a query](#openweather-api)
or [passed during `rest` fetcher initialization](#currency-api).

## Usage

/// tab | cli
```bash
echo 'SELECT id, name AS model, data.color AS color FROM objects' > query.sql
garf query.sql --source rest \
  --source.endpoint=https://api.restful-api.dev \
  --output csv
```
///

/// tab | python
```python
from garf.core.fetchers import RestApiReportFetcher
from garf.io import writer

fetcher = RestApiReportFetcher(endpoint='https://api.restful-api.dev')
query = 'SELECT id, name AS model, data.color AS color FROM objects'
report = fetcher.fetch(query)

writer.create_writer('csv').write(report, 'api_data')
```
///

## Examples

### OpenWeather API

!!!important
    To run the example below use generate [OpenWeather Map API key](https://openweathermap.org/appid).

OpenWeather expects API key to be added as a query parameter, so it should be
included as a macro in the query (in `WHERE` section).

/// tab | cli
```bash
echo """
SELECT
  main.temp AS temperature,
  weather[0].main AS weather
FROM weather
WHERE lat={lat}
  AND lon={lon}
  AND appid={api_key}
" > weather.sql

garf weather.sql --source rest \
  --source.endpoint=https://api.openweathermap.org/data/2.5 \
  --macro.api_key=OPEN_WEATHER_MAP_API_KEY \
  --macro.lat=33.44 \
  --macro.lon=-94.04 \
  --output csv
```
///

/// tab | python
```python
from garf.core.fetchers import RestApiReportFetcher
from garf.io import writer

fetcher = RestApiReportFetcher(
  endpoint='https://api.openweathermap.org/data/2.5'
)
query = """
SELECT
  main.temp AS temperature,
  weather[0].main AS weather
FROM weather
WHERE lat={lat}
  AND lon={lon}
  AND appid={api_key}
"""
report = fetcher.fetch(
  query,
  args={
    'macro': {
      'api_key': OPEN_WEATHER_MAP_API_KEY,
      'lat': 33.44,
      'lon': -94.04,
    }
  }
)

writer.create_writer('csv').write(report, 'weather')
```
///

### Currency API

!!!important
    To run the example below use generate [Currency API key](https://currencyapi.com/docs).

Currency API expects API key to be added as a header, so it should be
included as a fetcher specific parameter (`--source.apikey` in CLI or `apikey`
parameter in `RestApiReportFetcher` constructor when using Python library).

/// tab | cli
```bash
echo """
SELECT
  data.{currency}.value AS rate
FROM latest
WHERE
  base_currency={base_currency}
  AND currencies={currency}
""" > currency.sql

garf currency.sql --source rest \
  --source.endpoint=https://api.currencyapi.com/v3 \
  --source.apikey=CURRENCY_API_KEY \
  --macro.base_currency=EUR \
  --macro.currency=USD \
  --output csv
```
///

/// tab | python
```python
from garf.core.fetchers import RestApiReportFetcher
from garf.io import writer

fetcher = RestApiReportFetcher(
  endpoint='https://api.currencyapi.com/v3',
  apikey=CURRENCY_API_KEY,
)
query = """
SELECT
  data.{currency}.value AS rate
FROM latest
WHERE
  base_currency={base_currency}
  AND currencies={currency}
"""
report = fetcher.fetch(
  query,
  args={
    'macro': {
      'base_currency': 'EUR',
      'currency': 'USD',
    }
  }
)

writer.create_writer('csv').write(report, 'currency')
```
///
