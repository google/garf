!!! important
    To save data to Pushgateway install `garf-io` with Pushgateway support

    ```bash
    pip install garf-io[pushgateway]
    ```


`pushgateway` writer allows you to publish `GarfReport` to a Pushgateway endpoint.

/// tab | cli
```bash
garf query.sql --source API_SOURCE \
  --output pushgateway
```
///

/// tab | python
```python
from garf.core import report
from garf.io.writers import pushgateway_writer

sample_report = report.GarfReport(results=[[1]], column_names=['one'])

writer = pushgateway_writer.PushgatewayWriter()
writer.write(sample_report, 'grouping_key')
```
///

## Parameters
### endpoint

By default writer pushes data to `http://localhost:9091/`.
You can overwrite it with `endpoint` parameter.

/// tab | cli
```bash hl_lines="3"
garf query.sql --source API_SOURCE \
  --output pushgateway \
  --pushgateway.endpoint=http://pushgateway:9091
```
///

/// tab | python
```python hl_lines="7"
from garf.core import report
from garf.io.writers import pushgateway_writer

sample_report = report.GarfReport(results=[[1]], column_names=['one'])

writer = pushgateway_writer.PushgatewayWriter(endpoint="http://pushgateway:9091")
writer.write(sample_report, 'grouping_key')
```
///

### namespace

Every metric pushes to Pushgateway is prefix with `garf_` prefix.
You can overwrite it with `namespace` parameter.

/// tab | cli
```bash hl_lines="3"
garf query.sql --source API_SOURCE \
  --output pushgateway \
  --pushgateway.namespace=my_garf
```
///

/// tab | python
```python hl_lines="7"
from garf.core import report
from garf.io.writers import pushgateway_writer

sample_report = report.GarfReport(results=[[1]], column_names=['one'])

writer = pushgateway_writer.PushgatewayWriter(namespace="my_garf")
writer.write(sample_report, 'grouping_key')
```
///

### job

By default all metrics is pushed into `garf` job.
You can overwrite it with `job` parameter.

/// tab | cli
```bash hl_lines="3"
garf query.sql --source API_SOURCE \
  --output pushgateway \
  --pushgateway.job=garf_job
```
///

/// tab | python
```python hl_lines="7"
from garf.core import report
from garf.io.writers import pushgateway_writer

sample_report = report.GarfReport(results=[[1]], column_names=['one'])

writer = pushgateway_writer.PushgatewayWriter(job="garf_job")
writer.write(sample_report, 'grouping_key')
```
///

### expose_metrics_with_zero_values

By default only metrics with non-zero values are pushed to Pushgateway.
You can overwrite it with `expose_metrics_with_zero_values` parameter.

/// tab | cli
```bash hl_lines="3"
garf query.sql --source API_SOURCE \
  --output pushgateway \
  --pushgateway.expose_metrics_with_zero_values
```
///

/// tab | python
```python hl_lines="7"
from garf.core import report
from garf.io.writers import pushgateway_writer

sample_report = report.GarfReport(results=[[1]], column_names=['one'])

writer = pushgateway_writer.PushgatewayWriter(expose_metrics_with_zero_values=True)
writer.write(sample_report, 'grouping_key')
```
///


## Query syntax

In order to expose metrics to Pushgateway you need to ensure that either field name
or alias should contain `metric` in it.
So given the query

```sql
SELECT
  dimension.name AS name,
  metric.name AS field1,
  name AS metric_field2
FROM resource
```

two metrics will be pushed to Pushgateway - `<namespace>_<job>_field1` and `<namespace>_<job>_field2`.

### Info metrics

If you query does not contains any metric all it's dimensions will be bundled
into `_info` metric (i.e. `<namespace>_<job>_info`) with a value of `1.0`.
`info` metrics are useful when you need to capture the mapping between various
attributes in an API but don't care about the actual value.
