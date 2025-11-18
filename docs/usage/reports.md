# GarfReport

`ApiReportFetcher.fetch` returns you an instance of `GarfReport` object.

It's a table like structure (resembling pandas DataFrame) which can easily be manipulated.

#### Iteration

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


#### Slicing

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

#### Converting

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
  value_column_output="list",
)

# convert `campaigns` to dictionary
# where values are another dictionary
campaigns_dict = campaigns.to_dict(
  key_column="campaign_id",
  value_column_output="dict",
)
```
```

#### Building

`GarfReport` can be easily built from pandas or polars data frame:

```python
import pandas as pd
import polars as pl

# Pandas
df = pd.DataFrame(data=[[1]], columns=["one"])
report = GarfReport.from_pandas(df)

# Polars
df = pl.DataFrame(data=[[1]], schema=["one"], orient='row')
report = GarfReport.from_polars(df)
```

#### Saving

`GarfReport` can be easily saved to local or remote storage:

```python
from garf_io import writer

# initialize CSV writer
csv_writer = writer.create_writer('csv', destination_folder="/tmp")

# save report using one of the writers
csv_writer.write(campaigns, destination="my_file_name")
```
