# Create API client for garf

ApiClient is responsible for sending request to an API based on the query.

## Define ApiClient class

Creating an API client is the easiest way of developing with `garf`.


`garf-core` library has a `BaseClient` which one mandatory method you need to implement `get_response`.

Your implementation should take an instance of `garf.core.query_editor.BaseQueryElements` class and return `garf.core.api_clients.GarfApiResponse`.

* `BaseQueryElements` contains various elements parsed from the query such as fields, sorts, filters, and resource to get data from.
* `GarfApiReponse` contains `results` property that should be a list of dictionary-like objects.


Let see and example implementation of `MyApiClient`.

```python
from garf.core import api_clients, query_editor

class MyApiClient(api_clients.BaseClient):

  def get_response(
    request: query_editor.BaseQueryElements,
    **kwargs: str
  ) -> api_clients.GarfApiResponse:
    results = ... # get results from your API somehow
    return api_clients.GarfApiResponse(results=results)
```

## Use with ApiReportFetcher

Once your ApiClient class is defined, you can use with built-in `ApiReportFetcher`.

```python
from garf.core import ApiReportFetcher

api_client = MyClient()
report_fetcher = ApiReportFetcher(api_client=api_client)
```
!!! note
    [Learn more](../usage/fetcher.md) about using `ApiReportFetcher`.
