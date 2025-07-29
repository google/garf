# Use garf as a library


## Fetch reports

> For simplicity we're going to use built-in `FakeApiClient` to mimic results from an API.

```python
from garf_core import ApiReportFetcher
from garf_core.api_clients import FakeApiClient

api_client = FakeApiClient(results=[{'campaign': {'id': 1, 'clicks': 10}}])
report_fetcher = FakeApiReportFetcher(api_client)

query_text = "SELECT campaign.id AS campaign_id, clicks FROM campaign"

report = report_fetcher.fetch(query_text)
```

### Parametrize fetching

```python
parametrized_query_text = """
  SELECT
      campaign.id AS campaign_id
  FROM campaign
  WHERE campaign.status = '{status}'
"""

active_campaigns = report_fetcher.fetch(
  parametrized_query_text,
  args={"macro": {
    "status": "ENABLED"
  }}
)
```

## Work with reports

With reports you can perform common operations are iterating over rows of report, slicing, and converting to different structures.


```python
# Slicing
report_10_rows = report[0:10]
report_one_column = report['campaign_id']

# Iteration
for row in report:
  print(row.campaign_id)

# Conversion
df = report.to_pandas()
report_dict = report.to_dict(key_column='campaign_id', value_column='clicks')
```

[:octicons-arrow-right-24: More information](../usage/reports.md)



## Write reports

Reports can be written to various destinations.


```python
from garf_io.writers import CsvWriter
writer = CsvWriter()

writer.write(report, 'campaigns')
```

[:octicons-arrow-right-24: More information](../usage/writers.md)
