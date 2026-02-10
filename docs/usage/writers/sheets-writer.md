`sheets` writer allows you to save `GarfReport` to Google Sheets.

!!! important
    To save data to Google Sheets install `garf-io` with Google Sheets support

    ```bash
    pip install garf-io[sheets]
    ```

    `garf` uses [gspread](https://docs.gspread.org/en/latest/) to write data to
    Google Sheets needs to be [configured](https://docs.gspread.org/en/latest/oauth2.html).




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

## Parameters

### spreadsheet_url

By default reports are saved to a new spreadsheet.
You can overwrite it with `spreadsheet_url` parameter.

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

# Create example report
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

# Create example report
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

# Create example report
sample_report = report.GarfReport(results=[[1]], column_names=['one'])

writer = sheets_writer.SheetsWriter(is_append=True)
writer.write(sample_report, 'query')
```
///

### credentials_file

`garf` uses [gspread](https://docs.gspread.org/en/latest/) to write data to
Google Sheets which expects credentials file in `~/.config/gspread` folder.

You can adjust it via `credentials_file` parameter.

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

# Create example report
sample_report = report.GarfReport(results=[[1]], column_names=['one'])

writer = sheets_writer.SheetsWriter(credentials_file='/path/to/credentials.json')
writer.write(sample_report, 'query')
```
///

### auth_mode

By default `garf` will try to authenticate with [user credentials](https://docs.gspread.org/en/latest/oauth2.html#for-end-users-using-oauth-client-id)
You can overwrite it via `auth_mode` parameter (which can be either `oauth` or `service_account`)

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

# Create example report
sample_report = report.GarfReport(results=[[1]], column_names=['one'])

writer = sheets_writer.SheetsWriter(auth_mode='service_account')
writer.write(sample_report, 'query')
```
///
