!!! important
    To save data to Firestore install `garf-io` with Firestore support

    ```bash
    pip install garf-io[firestore]
    ```


`firestore` writer allows you to publish `GarfReport` to a Firestore collection.

/// tab | cli
```bash
garf query.sql --source API_SOURCE \
  --output firestore
```
///

/// tab | python
```python
from garf.core import report
from garf.io.writers import firestore_writer

# Create example report
sample_report = report.GarfReport(results=[[1]], column_names=['one'])

writer = firestore_writer.FirestoreWriter()
writer.write(sample_report, 'collection_name')
```
///

## Parameters
### project

By default it takes project name from `GOOGLE_CLOUD_PROJECT` env variable.
You can overwrite it with `project` parameter.

/// tab | cli
```bash hl_lines="3"
garf query.sql --source API_SOURCE \
  --output firestore \
  --firestore.project=my-project
```
///

/// tab | python
```python hl_lines="7"
from garf.core import report
from garf.io.writers import firestore_writer

# Create example report
sample_report = report.GarfReport(results=[[1]], column_names=['one'])

writer = firestore_writer.FirestoreWriter(project='my-project')
writer.write(sample_report, 'collection_name')
```
///

### db

By default it writes data to `(default)` db.
You can overwrite it with `db` parameter.

/// tab | cli
```bash hl_lines="3"
garf query.sql --source API_SOURCE \
  --output firestore \
  --firestore.db=garf_db
```
///

/// tab | python
```python hl_lines="7"
from garf.core import report
from garf.io.writers import firestore_writer

# Create example report
sample_report = report.GarfReport(results=[[1]], column_names=['one'])

writer = firestore_writer.FirestoreWriter(db="garf_db")
writer.write(sample_report, 'collection_name')
```
///
