!!! important
    To save data to Google Sheets install `garf-io` with Google Sheets support

    ```bash
    pip install garf-io[sheets]
    ```


`sheets` writer allows you to save `GarfReport` to Google Sheets.

/// tab | cli
```bash
garf query.sql --source API_SOURCE \
  --output sheets
```
///

/// tab | python
```python
from garf.core import report
from garf.io.writers import sheets_writer

# Create example report
sample_report = report.GarfReport(results=[[1]], column_names=['one'])

writer = sheets_writer.SheetsWriter()
writer.write(sample_report, 'query')
```
///
