!!! important
    To save data to DuckDB install `garf-io` with DuckDB support

    ```bash
    pip install garf-io[duckdb]
    ```


`duckdb` writer allows you to save `GarfReport` to DuckDB database.

/// tab | cli
```bash
garf query.sql --source API_SOURCE \
  --output duckdb
```
///

/// tab | python
```python
from garf.core import report
from garf.io.writers import duckdb_writer

# Create example report
sample_report = report.GarfReport(results=[[1]], column_names=['one'])

writer = duckdb_writer.DuckDBWriter(db=DUCKDB_FILE_PATH)
writer.write(sample_report, 'query')
```
///
