!!! important
    To save data to ClickHouse install `garf-io` with ClickHouse support

    ```bash
    pip install garf-io[clickhouse]
    ```


`clickhouse` writer allows you to save `GarfReport` to ClickHouse database.

/// tab | cli
```bash
garf query.sql --source API_SOURCE \
  --output clickhouse
```
///

/// tab | python
```python
from garf.core import report
from garf.io.writers import clickhouse_writer

# Create example report
sample_report = report.GarfReport(results=[[1]], column_names=['one'])

writer = clickhouse_writer.ClickHouseWriter(
  host='localhost',
  database='default',
)
writer.write(sample_report, 'query')
```
///

## Parameters

### host

URL of running Clickhouse instance - default is `localhost`.
Can be set with env variable `CLICKHOUSE_HOST`.

### port

Port of running Clickhouse instance - default is `8123`.
Can be set with env variable `CLICKHOUSE_PORT`.

### database

Name of Clickhouse database - default is `default`.
If databases does not exist, it will be created by garf before writing data.

### username

Name of user for Clickhouse database - default is `default`.
Can be set with env variable `CLICKHOUSE_USER`.

### password

Password for selected user - empty string by default.
Can be set with env variable `CLICKHOUSE_PASSWORD`.

### secure

Whether to establish secure connection to Clickhouse.

### if_exists

Action when table with the same name already exists in Clickhouse.
One of: `replace`, `append`.
