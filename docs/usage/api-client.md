# API clients

ApiClient is responsible for sending request to an API based on the query.

## Built-in API clients

### Fake

`FakeApiClient` is ideal for prototyping and test.

It allows you to specify sample response from an API as JSON or a dictionary.

```python
from garf.core.api_clients import FakeApiClient

fake_data = [
  {'field1': {'subfield': 1}, 'field2': 2},
  {'field1': {'subfield': 10}, 'field2': 2},
]
api_client = FakeApiClient(results=fake_data)
```

Instead of providing data as a variable you can read them from JSON or CSV.

```python
from garf.core.api_clients import FakeApiClient

api_client = FakeApiClient.from_json('path/to/json')
api_client = FakeApiClient.from_csv('path/to/csv')
```
!!! note
    You can simplify fetching fake data with [`FakeApiReportFetcher`](fetcher.md#fake).


### REST

REST API client is useful when you have a REST API available. Provide endpoint
to get data from.

```python
from garf.core.api_clients import RestApiClient

endpoint= 'https://api.restful-api.dev'
api_client = RestApiClient(endpoint=endpoint)
```

!!! note
    You can simplify fetching from REST API with [`RestApiReportFetcher`](fetcher.md#rest).

## Create API client

If you want to get reports from different APIs you need to implement new API Client.

Please refer to [development docs](../development/create-api-client.md) to learn more.
