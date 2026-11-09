`sheets` writer allows you to save `GarfReport` to Google Sheets.

!!! important
    To save data to Google Sheets install `garf-io` with Google Sheets support

    ```bash
    pip install garf-io[sheets]
    ```


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

sample_report = report.GarfReport(results=[[1]], column_names=['one'])

writer = sheets_writer.SheetsWriter()
writer.write(sample_report, 'query')
```
///

## Parameters

### spreadsheet_url

By default reports are saved to a new spreadsheet.
You can overwrite it with `spreadsheet_url` parameter.
If no url is provided new spreadsheet will be created.

/// tab | cli
```bash hl_lines="3"
garf query.sql --source API_SOURCE \
  --output sheets \
  --sheets.spreadsheet_url=SPREADSHEET_URL
```
///

/// tab | python
```python hl_lines="7"
from garf.core import report
from garf.io.writers import sheets_writer

sample_report = report.GarfReport(results=[[1]], column_names=['one'])

writer = sheets_writer.SheetsWriter(spreadsheet_url=SPREADSHEET_URL)
writer.write(sample_report, 'query')
```
///

### share_with

If you want to share created or existing spreadsheet, you can specify email(s)
via `share_with` parameter.

/// tab | cli
```bash hl_lines="3"
garf query.sql --source API_SOURCE \
  --output sheets \
  --sheets.share_with=your@email.com
```
///

/// tab | python
```python hl_lines="7"
from garf.core import report
from garf.io.writers import sheets_writer

sample_report = report.GarfReport(results=[[1]], column_names=['one'])

writer = sheets_writer.SheetsWriter(share_with='your@email.com')
writer.write(sample_report, 'query')
```
///

### is_append

By default new report overwrites old report in worksheets.
You can adjust this behaviour with `is_append` parameter.

/// tab | cli
```bash hl_lines="3"
garf query.sql --source API_SOURCE \
  --output sheets \
  --sheets.is_append
```
///

/// tab | python
```python hl_lines="7"
from garf.core import report
from garf.io.writers import sheets_writer

sample_report = report.GarfReport(results=[[1]], column_names=['one'])

writer = sheets_writer.SheetsWriter(is_append=True)
writer.write(sample_report, 'query')
```
///

### credentials_file

`credentials_file` allows you to specify how to connect to Sheets via API.

/// tab | cli
```bash hl_lines="3"
garf query.sql --source API_SOURCE \
  --output sheets \
  --sheets.credentials_file=/path/to/credentials.json
```
///

/// tab | python
```python hl_lines="7"
from garf.core import report
from garf.io.writers import sheets_writer

sample_report = report.GarfReport(results=[[1]], column_names=['one'])

writer = sheets_writer.SheetsWriter(credentials_file='/path/to/credentials.json')
writer.write(sample_report, 'query')
```
///

### auth_mode

You can set select one of `auth_mode` modes -  `oauth`,
`service_account` or `adc` (Application Default Credentials).

/// tab | cli
```bash hl_lines="3"
garf query.sql --source API_SOURCE \
  --output sheets \
  --sheets.auth_mode=service_account
```
///

/// tab | python
```python hl_lines="7"
from garf.core import report
from garf.io.writers import sheets_writer

sample_report = report.GarfReport(results=[[1]], column_names=['one'])

writer = sheets_writer.SheetsWriter(auth_mode='service_account')
writer.write(sample_report, 'query')
```
///

### folder_id

By default reports are saved to root folder of Drive.
You can overwrite it with `folder_id` parameter.

/// tab | cli
```bash hl_lines="3"
garf query.sql --source API_SOURCE \
  --output sheets \
  --sheets.folder_id=FOLDER_ID
```
///

/// tab | python
```python hl_lines="7"
from garf.core import report
from garf.io.writers import sheets_writer

sample_report = report.GarfReport(results=[[1]], column_names=['one'])

writer = sheets_writer.SheetsWriter(folder_id=FOLDER_ID)
writer.write(sample_report, 'query')
```
///

### spreadsheet_name

If new spreadsheet is created (when `spreadsheet_url` is not provided) `garf` will
name is `Garf SOME RANDOM_STRING`.
You can overwrite it with `spreadsheet_name` parameter.

/// tab | cli
```bash hl_lines="3"
garf query.sql --source API_SOURCE \
  --output sheets \
  --sheets.spreadsheet_name=my_data
```
///

/// tab | python
```python hl_lines="7"
from garf.core import report
from garf.io.writers import sheets_writer

sample_report = report.GarfReport(results=[[1]], column_names=['one'])

writer = sheets_writer.SheetsWriter(spreadsheet_name='my_data')
writer.write(sample_report, 'query')
```
///
