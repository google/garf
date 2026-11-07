!!! important
    To save data to Neo4j install `garf-io` with Neo4j support

    ```bash
    pip install garf-io[neo4j]
    ```


`neo4j` writer allows you to save `GarfReport` to a Neo4j graph database.
Each row in the report becomes a node, and relationships are created between consecutive nodes.

/// tab | cli
```bash
garf query.sql --source API_SOURCE \
  --output neo4j
```
///

/// tab | python
```python
from garf.core import report
from garf.io.writers import neo4j_writer

# Create example report
sample_report = report.GarfReport(results=[[1, 'Alice', 30]], column_names=['id', 'name', 'age'])

writer = neo4j_writer.Neo4jWriter(
  uri='bolt://localhost:7687',
  username='neo4j',
  password='password',
)
writer.write(sample_report, 'employees')
```
///

## Parameters

### uri

Neo4j connection URI. Default is `bolt://localhost:7687`.
Can be set with env variable `NEO4J_URI`.

/// tab | cli
```bash hl_lines="3"
garf query.sql --source API_SOURCE \
  --output neo4j \
  --neo4j.uri=bolt://my-neo4j:7687
```
///

/// tab | python hl_lines="7"
```python hl_lines="8"
from garf.core import report
from garf.io.writers import neo4j_writer

writer = neo4j_writer.Neo4jWriter(uri='bolt://my-neo4j:7687')
```
///

### username

Username for Neo4j authentication. Default is `neo4j`.
Can be set with env variable `NEO4J_USERNAME`.

/// tab | cli
```bash hl_lines="3"
garf query.sql --source API_SOURCE \
  --output neo4j \
  --neo4j.username=admin
```
///

/// tab | python hl_lines="7"
```python hl_lines="8"
from garf.core import report
from garf.io.writers import neo4j_writer

writer = neo4j_writer.Neo4jWriter(username='admin')
```
///

### password

Password for Neo4j authentication. Default is empty string.
Can be set with env variable `NEO4J_PASSWORD`.

!!! warning
    Be careful when storing passwords in environment variables or configuration files.
    Consider using Neo4j's built-in authentication mechanisms for production.

/// tab | cli
```bash hl_lines="3"
garf query.sql --source API_SOURCE \
  --output neo4j \
  --neo4j.password=secret123
```
///

/// tab | python hl_lines="7"
```python hl_lines="8"
from garf.core import report
from garf.io.writers import neo4j_writer

writer = neo4j_writer.Neo4jWriter(password='secret123')
```
///

### database

Name of Neo4j database to write to. Default is `neo4j`.
Can be set with env variable `NEO4J_DATABASE`.

/// tab | cli
```bash hl_lines="3"
garf query.sql --source API_SOURCE \
  --output neo4j \
  --neo4j.database=mydb
```
///

/// tab | python hl_lines="7"
```python hl_lines="8"
from garf.core import report
from garf.io.writers import neo4j_writer

writer = neo4j_writer.Neo4jWriter(database='mydb')
```
///

### label_prefix

Prefix to add to node labels. By default, labels are constructed from column names.

/// tab | cli
```bash hl_lines="3"
garf query.sql --source API_SOURCE \
  --output neo4j \
  --neo4j.label_prefix=Custom
```
///

/// tab | python hl_lines="7"
```python hl_lines="8"
from garf.core import report
from garf.io.writers import neo4j_writer

writer = neo4j_writer.Neo4jWriter(label_prefix='Custom')
```
///

### relationship_type

Custom relationship type to use between nodes. By default, the destination name is used.

/// tab | cli
```bash hl_lines="3"
garf query.sql --source API_SOURCE \
  --output neo4j \
  --neo4j.relationship_type=WORKS_WITH
```
///

/// tab | python hl_lines="7"
```python hl_lines="8"
from garf.core import report
from garf.io.writers import neo4j_writer

writer = neo4j_writer.Neo4jWriter(relationship_type='WORKS_WITH')
```
///

### if_exists

Action when nodes with the same properties already exist in Neo4j.
One of: `merge`, `create`, `delete`.

* `merge` (default) - Merge nodes with same properties using MERGE clause
* `create` - Always create new nodes, ignoring existing ones
* `delete` - Delete existing nodes before inserting new ones

/// tab | cli
```bash hl_lines="3"
garf query.sql --source API_SOURCE \
  --output neo4j \
  --neo4j.if-exists=create
```
///

/// tab | python hl_lines="7"
```python hl_lines="8"
from garf.core import report
from garf.io.writers import neo4j_writer

writer = neo4j_writer.Neo4jWriter(if_exists='create')
```
///

### relationship_properties

Optional additional properties to add to relationships between nodes.
Pass as a dictionary of property name and value.

/// tab | cli
```bash hl_lines="3"
garf query.sql --source API_SOURCE \
  --output neo4j \
  --neo4j.relationship_properties={'date': '2024-01-01'}
```
///

/// tab | python hl_lines="7"
```python hl_lines="8"
from garf.core import report
from garf.io.writers import neo4j_writer

writer = neo4j_writer.Neo4jWriter(
  relationship_properties={'date': '2024-01-01'}
)
```
///

## Data Model

The Neo4j writer transforms report data into a graph structure:

### Nodes
Each row in the report becomes a node with:
* **Labels**: Constructed from `label_prefix` (if provided) and column names
* **Properties**: All columns from the report row

Example:
```
Data: [[1, 'Alice', 30]]
Columns: ['id', 'name', 'age']
Result: (:Node:id:name:age) with properties {id: 1, name: 'Alice', age: 30}
```

### Relationships
Relationships are created between consecutive rows:
* **Type**: Based on `relationship_type` option or destination name
* **Direction**: From first row to subsequent rows

Example:
```
Data: [[1, 'Alice'], [2, 'Bob'], [3, 'Charlie']]
Result:
(:Node:id)-[:RELATIONSHIP:id]->(:Node:id)
(:Node:id)-[:RELATIONSHIP:id]->(:Node:id)
```

## Environment Variables

All parameters can be set via environment variables:

| Parameter | Environment Variable | Default |
|-----------|---------------------|---------|
| `uri` | `NEO4J_URI` | `bolt://localhost:7687` |
| `username` | `NEO4J_USERNAME` | `neo4j` |
| `password` | `NEO4J_PASSWORD` | `` |
| `database` | `NEO4J_DATABASE` | `neo4j` |

/// tab | cli
```bash
export NEO4J_URI='bolt://my-neo4j:7687'
export NEO4J_USERNAME='admin'
export NEO4J_PASSWORD='secret'
garf query.sql --source API_SOURCE --output neo4j
```
///

## Notes

* The writer supports the standard `prefix` and `suffix` options for dynamic destination naming
* Array handling and date handling options are inherited from the base writer
* Empty reports are handled gracefully - no nodes are created
* The writer automatically closes the connection when the `close()` method is called
