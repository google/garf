# `garf_core` built-in funtionality

Apart from defining such interfaces as `BaseApiClient`, `BaseParser`, `ApiReportFetcher`, etc.
`garf_core` comes with several built-in implementations.

## Parsers

* `ListParser` - returns results from API as a raw list.
* `DictParser` - returns results from API as a formatted dict.
* `NumericDictParser` - returns results from API as a formatted dict with converted numeric values.

## ApiClients

* `FakeApiClient` - initializes API responses based on some predefined set of data. \
  You can either pass data to it directly (as a list of dicts) or load them from JSON / CSV file.

  ```python
  from garf_core.api_clients import FakeApiClient


  api_client = FakeApiClient(data=[{'field': 'value'}]
  api_client = FakeApiClient.from_csv('path/to/csv')
  api_client = FakeApiClient.from_json('path/to/json')
  ```

* `RestApiClient` - gets data from remote / local API endpoint.
  ```python
  from garf_core.api_clients import RestApiClient


  api_client = RestApiClient(endpoint='http://localhost:3000/api/resource')
  ```

## ApiReportFetchers

* `FakeApiReportFetcher` - fetches data based on provided data or load them from csv / json file.

  ```python
  from garf_core.fetchers import FakeApiReportFetcher


  fetcher = FakeApiApiReportFetcher(data=[{'field': 'value'}]
  fetcher = FakeApiApiReportFetcher.from_csv('path/to/csv')
  fetcher = FakeApiApiReportFetcher.from_json('path/to/json')
  ```
* `RestApiReportFetcher` - fetches data from specified API endpoint.

  ```python
  from garf_core.fetchers import RestApiReportFetcher


  fetcher = RestApiApiReportFetcher(endpoint='http://localhost:8000/api/resource')
  ```
