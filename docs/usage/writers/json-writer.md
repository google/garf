`json` writer allows you to save `GarfReport` as JSON or JSONL file to local or remote storage.

/// tab | cli
```bash
garf query.sql --source API_SOURCE \
  --output json
```
///

/// tab | python
```python
from garf.core import report
from garf.io.writers import json_writer

# Create example report
sample_report = report.GarfReport(results=[[1]], column_names=['one'])

writer = json_writer.JsonWriter()
writer.write(sample_report, 'query')
```
///

## Parameters

### Destination folder

You can specify the local or remote folder to store results.
I.e. if you want to write results to Google Cloud Storage bucket `gs://PROJECT_ID/bucket`,
you need to provide `destination_folder` parameter.


/// tab | cli
```bash hl_lines="3"
garf query.sql --source API_SOURCE \
  --output json \
  --json.destination-folder=gs://PROJECT_ID/bucket
```
///

/// tab | python
```python
from garf.core import report
from garf.io.writers import json_writer

# Create example report
sample_report = report.GarfReport(results=[[1]], column_names=['one'])

writer = json_writer.JsonWriter(destination_folder='gs://PROJECT_ID/bucket/')
writer.write(sample_report, 'query')
```
///

### Format

You can specify the output format:

* `json` - JSON (default)
* `jsonl` - JSON lines

/// tab | cli
```bash hl_lines="3"
garf query.sql --source API_SOURCE \
  --output json \
  --json.format=jsonl
```
///

/// tab | python
```python hl_lines="7"
from garf.core import report
from garf.io.writers import json_writer

# Create example report
sample_report = report.GarfReport(results=[[1]], column_names=['one'])

writer = json_writer.JsonWriter(format='jsonl')
writer.write(sample_report, 'query')
```
///
