`csv` writer allows you to save `GarfReport` as a CSV file to local or remote storage.

/// tab | cli
```bash
garf query.sql --source API_SOURCE \
  --output csv
```
///

/// tab | python
```python
from garf.core import report
from garf.io.writers import csv_writer

# Create example report
sample_report = report.GarfReport(results=[[1]], column_names=['one'])

writer = csv_writer.CsvWriter()
writer.write(sample_report, 'query')
```
///

## Parameters

### Destination folder

For `csv` writer you can specify the local or remote folder to store results.
I.e. if you want to write results to Google Cloud Storage bucket `gs://PROJECT_ID/bucket`,
you need to provide `destination_folder` parameter.


/// tab | cli
```bash hl_lines="3"
garf query.sql --source API_SOURCE \
  --output csv \
  --csv.destination-folder=gs://PROJECT_ID/bucket
```
///

/// tab | python
```python
from garf.core import report
from garf.io.writers import csv_writer

# Create example report
sample_report = report.GarfReport(results=[[1]], column_names=['one'])

writer = csv_writer.CsvWriter(destination_folder='gs://PROJECT_ID/bucket/')
writer.write(sample_report, 'query')
```
///
