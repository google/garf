# Use garf as a library

## Installation

1. create virtual environment and install the tool

```
python3 -m venv garf
source garf/bin/activate
pip install garf-core garf-io
```
> Depending on your needs you might want to install additional libraries for [fetching](../libs/garf_community/) and [writing](../libs/garf_io/) data.


### initialize subclass `ApiReportFetcher` to get reports

> For simplicity we're going to use built-in `FakeApiReportFetcher`.

```python
from garf_core.fetchers import FakeApiReportFetcher

report_fetcher = FakeApiReportFetcher(data=[{'campaign': {'id': 1, 'clicks': 10}}])

# create query text
query_text = "SELECT campaign.id AS campaign_id FROM campaign"

campaigns = report_fetcher.fetch(query_text)
```

#### Use macros in your queries

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

#### Define queries

There are three ways how you can define a query:
* in a variable
* in a file
* in a class (useful when you have complex parametrization and validation)

```python
from garf_core.base_query import BaseQuery
from garf_io import reader


# 1. define query as a string an save in a variable
query_string = "SELECT campaign.id FROM campaign"

# 2. define path to a query file and read from it
# path can be local
query_path = "path/to/query.sql"
# or remote
query_path = "gs://PROJECT_ID/path/to/query.sql"

# Instantiate reader
reader_client = reader.FileReader()
# And read from the path
query = reader_client.read(query_path)

# 3. define query as a class

# Native style
class Campaigns(BaseQuery):
  query_text  = """
    SELECT
      campaign.id
    FROM campaign
    WHERE campaign.status = {status}
    """

  def __init__(self, status: str = "ENABLED") -> None:
    self.status = status

# Dataclass style
from dataclasses import dataclass

@dataclass
class Campaigns(BaseQuery):
  query_text  = """
    SELECT
      campaign.id
    FROM campaign
    WHERE campaign.status = {status}
    """
  status: str = "ENABLED"

# Old style
class Campaigns(BaseQuery):
  def __init__(self, status: str = "ENABLED"):
    self.query_text = f"""
    SELECT
      campaign.id
    FROM campaign
    WHERE campaign.status = {status}
    """

active_campaigns = report_fetcher.fetch(Campaigns())
inactive_campaigns = report_fetcher.fetch(Campaigns("INACTIVE"))
```

#### Iteration and slicing

`ApiReportFetcher.fetch` method returns an instance of `GarfReport` object which you can use to perform simple iteration.

```python
query_text = "SELECT campaign.id AS campaign_id, clicks FROM campaign"
campaigns = report_fetcher.fetch(query_text)

# iterate over each row of `campaigns` report
for row in campaigns:
  # Get element as an attribute
  print(row.campaign_id)

  # Get element as a slice
  print(row["campaign_id"])

  # Get element as an index
  print(row[0])

  # Create new column
  row["new_campaign_id"] = row["campaign_id"] + 1
```


You can easily slice the report

```python
# Create new reports by selecting one or more columns
campaign_only_report = campaigns["campaign_id"]
campaign_name_clicks_report = campaigns[["campaign_id", "clicks"]]

# Get subset of the report
# Get first row only
first_campaign_row = campaigns[0]
# Get first ten rows from the report
first_10_rows_from_campaigns = campaigns[0:10]
```

#### Convert report

`GarfReport` can be easily converted to common data structures:

```python
# convert `campaigns` to list of lists
campaigns_list = campaigns.to_list()

# convert `campaigns` to flatten list
campaigns_list = campaigns.to_list(row_type="scalar")

# convert `campaigns` column campaign_id to list
campaigns_list = campaigns["campaign_id"].to_list()

# convert `campaigns` column campaign_id to list with unique values
campaigns_list = campaigns["campaign_id"].to_list(distinct=True)

# convert `campaigns` to list of dictionaries
# each dictionary maps report column to its value, i.e.
# {"campaign_name": "test_campaign", "campaign_id": 1, "clicks": 10}
campaigns_list = campaigns.to_list(row_type="dict")

# convert `campaigns` to pandas DataFrame
campaigns_df = campaigns.to_pandas()

# convert `campaigns` to polars DataFrame
campaigns_df = campaigns.to_polars()

# convert `campaigns` to dictionary
# map campaign_id to campaign_name one-to-one
campaigns_dict = campaigns.to_dict(
  key_column="campaign_id",
  value_column="clicks",
  value_column_output="scalar",
)

# convert `campaigns` to dictionary
# map campaign_id to campaign_name one-to-many
campaigns_dict = campaigns.to_dict(
  key_column="campaign_id",
  value_column="clicks",
  value_column_output="list",
)
```

#### Build report

`GarfReport` can be easily built from pandas or polars data frame:

```
import pandas as pd
import polars as pl

# Pandas
df = pd.DataFrame(data=[[1]], columns=["one"])
report = GarfReport.from_pandas(df)

# Polars
df = pl.DataFrame(data=[[1]], schema=["one"], orient='row')
report = GarfReport.from_polars(df)
```

#### Save report

`GarfReport` can be easily saved to local or remote storage:

```python
from garf_io import writer

# initialize CSV writer
csv_writer = writer.create_writer('csv', destination_folder="/tmp")

# save report using one of the writers
csv_writer.write(campaigns, destination="my_file_name")
```

Learn more about available writers at [`garf-io` documentation](../libs/garf_io/README.md).

### Combine fetching and saving with `ApiQueryExecutor`

Ensure that `garf-executors` library is installed:

```
pip install garf-executors
```

If your job is to execute query and write it to local/remote storage you can use `ApiQueryExecutor` to do it easily.
> When reading query from file `ApiQueryExecutor` will use query file name as a name for output file/table.
```python
from garf_core.fetchers import FakeApiReportFetcher
from garf_executors import api_executor
from garf_io import reader


# initialize query_executor to fetch report and store them in local/remote storage
fake_report_fetcher = FakeApiReportFetcher(data=[{'campaign': {'id': 1}}])

query_executor = api_executor.ApiQueryExecutor(fetcher=fake_report_fetcher)

context = api_executor.ApiExecutionContext(writer='csv')


query_text = "SELECT campaign.id AS campaign_id, FROM campaign"

# execute query and save results to `campaign.csv`
query_executor.execute(query=query_text, title="campaign", context=context)

# execute query from file and save to results to `/tmp/query.csv`
reader_client = reader.FileReader()
query_path="path/to/query.sql"

query_executor.execute(
    query=reader_client.read(query_path),
    title=query_path,
    context=context
)
```

## Disclaimer
This is not an officially supported Google product.
