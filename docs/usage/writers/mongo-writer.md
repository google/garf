!!! important
    To save data to MongoDB install `garf-io` with MongoDB support

    ```bash
    pip install garf-io[mongo]
    ```


`mongo` writer allows you to publish `GarfReport` to a MongoDB collection.

/// tab | cli
```bash
garf query.sql --source API_SOURCE \
  --output mongo
```
///

/// tab | python
```python
from garf.core import report
from garf.io.writers import mongo_writer

# Create example report
sample_report = report.GarfReport(results=[[1]], column_names=['one'])

writer = mongo_writer.MongoDBWriter()
writer.write(sample_report, 'collection_name')
```
///

## Parameters
### connection_string

By default it connects to `mongodb://localhost:27017/`.
You can overwrite it with `connection_string` parameter.

/// tab | cli
```bash hl_lines="3"
garf query.sql --source API_SOURCE \
  --output mongo \
  --mongo.connection_string=mongodb://mongo:27017
```
///

/// tab | python
```python hl_lines="7"
from garf.core import report
from garf.io.writers import mongo_writer

# Create example report
sample_report = report.GarfReport(results=[[1]], column_names=['one'])

writer = mongo_writer.MongoDbWriter(connection_string="mongodb://mongo:27017")
writer.write(sample_report, 'collection_name')
```
///

### db

By default it writes data to `garf` db.
You can overwrite it with `db` parameter.

/// tab | cli
```bash hl_lines="3"
garf query.sql --source API_SOURCE \
  --output mongo \
  --mongo.db=my_garf
```
///

/// tab | python
```python hl_lines="7"
from garf.core import report
from garf.io.writers import mongo_writer

# Create example report
sample_report = report.GarfReport(results=[[1]], column_names=['one'])

writer = mongo_writer.MongoDbWriter(db="my_garf")
writer.write(sample_report, 'collection_name')
```
///
