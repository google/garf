`drive` writer allows you to save `GarfReport` to Google Drive.

!!! important
    To save data to Google Drive install `garf-io` with Google Drive support

    ```bash
    pip install garf-io[drive]
    ```

/// tab | cli
```bash
garf query.sql --source API_SOURCE \
  --output drive
```
///

/// tab | python
```python
from garf.core import report
from garf.io.writers import drive_writer

sample_report = report.GarfReport(results=[[1]], column_names=['one'])

writer = drive_writer.GoogleDriveWriter()
writer.write(sample_report, 'query')
```
///

## Parameters

### share_with

If you want to share created files with someone, you can specify email(s)
via `share_with` parameter.

/// tab | cli
```bash hl_lines="3"
garf query.sql --source API_SOURCE \
  --output drive \
  --drive.share_with=your@email.com
```
///

/// tab | python
```python hl_lines="7"
from garf.core import report
from garf.io.writers import drive_writer

sample_report = report.GarfReport(results=[[1]], column_names=['one'])

writer = drive_writer.GoogleDriveWriter(share_with='your@email.com')
writer.write(sample_report, 'query')
```
///


### credentials_file

`credentials_file` allows you to specify how to connect to Drive via API.

/// tab | cli
```bash hl_lines="3"
garf query.sql --source API_SOURCE \
  --output drive \
  --drive.credentials_file=/path/to/credentials.json
```
///

/// tab | python
```python hl_lines="7"
from garf.core import report
from garf.io.writers import drive_writer

sample_report = report.GarfReport(results=[[1]], column_names=['one'])

writer = drive_writer.GoogleDriveWriter(credentials_file='/path/to/credentials.json')
writer.write(sample_report, 'query')
```
///

### auth_mode

By default `garf` will try to authenticate with [user credentials](https://docs.gspread.org/en/latest/oauth2.html#for-end-users-using-oauth-client-id)
You can overwrite it via `auth_mode` parameter (which can be `oauth`,
`service_account` or `adc` (Application Default Credentials))

/// tab | cli
```bash hl_lines="3"
garf query.sql --source API_SOURCE \
  --output drive \
  --drive.auth_mode=service_account
```
///

/// tab | python
```python hl_lines="7"
from garf.core import report
from garf.io.writers import drive_writer

sample_report = report.GarfReport(results=[[1]], column_names=['one'])

writer = drive_writer.GoogleDriveWriter(auth_mode='service_account')
writer.write(sample_report, 'query')
```
///

### folder_id

By default reports are saved to root folder of Drive.
You can overwrite it with `folder_id` parameter.

/// tab | cli
```bash hl_lines="3"
garf query.sql --source API_SOURCE \
  --output drive \
  --drive.folder_id=FOLDER_ID
```
///

/// tab | python
```python hl_lines="7"
from garf.core import report
from garf.io.writers import drive_writer

sample_report = report.GarfReport(results=[[1]], column_names=['one'])

writer = drive_writer.GoogleDriveWriter(folder_id=FOLDER_ID)
writer.write(sample_report, 'query')
```
///
