!!! important
    To save data to Excel install `garf-io` with Excel support

    ```bash
    pip install garf-io[excel]
    ```


`excel` writer allows you to save `GarfReport` to Excel files.

/// tab | cli
```bash
garf query.sql --source API_SOURCE \
  --output excel
```
///

/// tab | python
```python
from garf.core import report
from garf.io.writers import excel_writer

# Create example report
sample_report = report.GarfReport(results=[[1]], column_names=['one'])

writer = excel_writer.ExcelWriter()
writer.write(sample_report, 'query')
```
///

## Parameters
### Destination Folder

By default reports are saved to current working directory.
You can overwrite it with `destination_folder` parameter.

/// tab | cli
```bash hl_lines="3"
garf query.sql --source API_SOURCE \
  --output excel \
  --excel.destination_folder=/path/to/folder
```
///

/// tab | python
```python hl_lines="7"
from garf.core import report
from garf.io.writers import excel_writer

# Create example report
sample_report = report.GarfReport(results=[[1]], column_names=['one'])

writer = excel_writer.ExcelWriter(destination_folder="/path/to/folder")
writer.write(sample_report, 'query')
```
///

### File

You can specify a single file to write multiple reports (sheets) to using the `file` parameter.
When `file` is specified, the destination argument in `write` becomes the sheet name.

/// tab | cli
```bash hl_lines="3"
garf query.sql --source API_SOURCE \
  --output excel \
  --excel.file=report.xlsx
```
///

/// tab | python
```python hl_lines="7"
from garf.core import report
from garf.io.writers import excel_writer

# Create example report
sample_report = report.GarfReport(results=[[1]], column_names=['one'])

writer = excel_writer.ExcelWriter(file="report.xlsx")
writer.write(sample_report, 'sheet_name')
```
///
