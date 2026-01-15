# ApiReportFetcher

ApiReportFetcher is reponsible for getting report from an API based on provided query.

## Initialization

### Api Client
To initialize `ApiReportFetcher` you need an instance of an API client to
interact with an API. You can choose from [built-in](api-client.md) API clients
or [create](../development/create-api-client.md) your own.
```python
from garf.core import ApiReportFetcher

report_fetcher = ApiReportFetcher(api_client)
```


### Parser

Under the hood `ApiReportFetcher` fetches data from an API as list of
dictionaries and tries to access elements in each dictionary via `DictParser`.

You can overwrite this behaviour by using one of [built-in parsers](parsers.md)
or [implementing](../development/create-api-response-parser.md) your own.

Suppose you want to use `NumericConverterDictParser` to automatically convert
strings to int/float whenever possible.


```python
from garf.core import ApiReportFetcher
from garf.core.parsers import NumericConverterDictParser

report_fetcher = ApiReportFetcher(
  api_client=api_client,
  parser=NumericConverterDictParser
)
```


### Built-in queries

Some queries for a particular API can be quite common so you want to create one
or several [built-in queries](queries.md#built-in-queries).

You can specified them in `builtin_queries` parameters during `ApiReportFetcher`
initialization.

```python
from garf.core import ApiReportFetcher
from garf.core.report import GarfReport
from garf.core.parsers import NumericConverterDictParser

def builtin_query(fetcher: ApiReportFetcher) -> GarfReport:
  return fetcher.fetch('SELECT field FROM resource')


builtin_queries = {'my_query': builtin_query}

report_fetcher = ApiReportFetcher(
  api_client=api_client,
  builtin_queries=builtin_queries
)
```


## Fetching
To fetch data from an API use `fetch` method.

```python
from garf.core import ApiReportFetcher

report_fetcher = ApiReportFetcher(api_client)
query = 'SELECT metric FROM resource'
report = report_fetcher.fetch(query)
```

!!!note
    You can use `afetch` method to run execute the query asynchronously
    ```python
    report = await report_fetcher.afetch(query)
    ```

`fetch` method returns `GarfReport` which can be [processed](reports.md)  in Python
or [written](writers.md) to local / remote storage.

### Parametrization

If your query contains [macros](queries.md/#macros)  or [templates](queries.md#templates), you need to pass values for them via `args` parameters.

```python
from garf.core import ApiReportFetcher
from garf.core.query_editor import GarfQueryParameters

report_fetcher = ApiReportFetcher(api_client)

query = 'SELECT metric FROM resource WHERE dimension={dimension}'

query_parameters = GarfQueryParameters(
  macro={'dimension': 'value'},
  template={'dimension': 'value'},
)

report = report_fetcher.fetch(query, args=query_parameters)
```

!!! note
    You can pass a dictionary instead of `GarfQueryParameters`.

    ```python

    query_parameters = {
      'macro': {
        'dimension': 'value',
      },
      'template': {
        'dimension': 'value',
      }
    }

    report = report_fetcher.fetch(query, args=query_parameters)
    ```

### Caching

You can store and retrieve reports from cache rather that getting them from API.


Cache has two default parameters which can be overwritten:

* `cache_path` (default is `$HOME/.garf/cache`)
* `cache_ttl_seconds` (default is 3600 seconds or 1 hour).

```python
from garf.core import ApiReportFetcher

report_fetcher = ApiReportFetcher(
  api_client,
  enable_cache=True,
  cache_path='~/.cache',
  cache_ttl_seconds=4*60*60
)

query = 'SELECT metric FROM resource'

report = report_fetcher.fetch(query)
```

## Built-in report fetchers

To simplify testing and working with REST APIs `garf` has two built-in report fetchers:

* `FakeApiReportFetcher` - simulates API response based on provided data
* `RestApiReportFetcher` - interacts with APIs with REST interface.

### Fake

`FakeApiReportFetcher` is based on [`FakeApiClient`](api-client.md#fake).

It's ideal for prototyping and testing APIs without interacting with them directly.

```python
from garf.core.fetchers import FakeApiReportFetcher

fake_data = [
  {'field1': {'subfield': 1}, 'field2': 2},
  {'field1': {'subfield': 10}, 'field2': 2},
]
report_fetcher = FakeApiReportFetcher.from_data(fake_data)

query = 'SELECT field1.subfield AS column FROM resource'
report = report_fetcher.fetch(query)
```

!!!note
    Instead providing data directly you can use helper methods - `from_json` and `from_csv`:

    ```python
    report_fetcher = FakeApiReportFetcher.from_json('path/to/json')
    report_fetcher = FakeApiReportFetcher.from_csv('path/to/csv')

    ```

### Rest

`RestApiReportFetcher` is based on [`RestApiClient`](api-client.md#rest).

It's can be used with any API that provides REST interface.

You need to provide `endpoint` parameter which specifies root level address where
API exists.

When writing queries specify relative address of the resource you want to fetch from
(i.e. `customers/1/orders`).

```python
from garf.core.fetchers import RestApiReportFetcher

endpoint= 'https://api.restful-api.dev'
report_fetcher = RestApiReportFetcher.from_endpoint(endpoint)

query = 'SELECT id FROM objects'
report = report_fetcher.fetch(query)
```
