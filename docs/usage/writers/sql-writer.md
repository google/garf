!!! important
    To save data to Google Sheets install `garf-io` with SqlAlchemy support

    ```bash
    pip install garf-io[sqlalchemy]
    ```


`sqldb` writer allows you to save `GarfReport` to SqlAlchemy supported table databases.

/// tab | cli
```bash
garf query.sql --source API_SOURCE \
  --output sqldb
```
///

/// tab | python
```python
from garf.core import report
from garf.io.writers import sqldb_writer

# Create example report
sample_report = report.GarfReport(results=[[1]], column_names=['one'])

writer = sqldb_writer.SqlAlchemyWriter(
  connection_string=SQLALCHEMY_CONNECTION_STRING
)
writer.write(sample_report, 'query')
```
///
