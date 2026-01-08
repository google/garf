`console` writer allows you to print `GarfReport` to standard output in the terminal.

/// tab | cli
```bash
garf query.sql --source API_SOURCE \
  --output console
```
///

/// tab | python
```python
from garf_core import report
from garf_io.writers import console_writer

# Create example report
sample_report = report.GarfReport(results=[[1]], column_names=['one'])

writer = console_writer.ConsoleWriter()
writer.write(sample_report, 'query')
```
///

##Parameters

### Format

For `console` writer you can specify the output format:

* `table` - rich table (default).
* `json` - JSON.
* `jsonl` - JSON lines

/// tab | cli
```bash hl_lines="3"
garf query.sql --source API_SOURCE \
  --output console \
  --console.format=json
```
///

/// tab | python
```python hl_lines="7"
from garf_core import report
from garf_io.writers import console_writer

# Create example report
sample_report = report.GarfReport(results=[[1]], column_names=['one'])

writer = console_writer.ConsoleWriter(format='json')
writer.write(sample_report, 'query')
```
///

### Page size

If you're using `console` writer with `table` format option, you can specify
`page_size` parameter to print N rows to the console.

/// tab | cli
```bash hl_lines="3"
garf query.sql --source API_SOURCE \
  --output console \
  --console.page-size=100
```
///

/// tab | python
```python hl_lines="7"
from garf_core import report
from garf_io.writers import console_writer

# Create example report
sample_report = report.GarfReport(results=[[1]], column_names=['one'])

writer = console_writer.ConsoleWriter(page_size=100)
writer.write(sample_report, 'query')
```
///
