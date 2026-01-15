If your API client returns lists of structures that are not similar to dictionaries,
you might need to implement a custom parser based on `garf.core.parsers.BaseParser`.


## Define Parser class

The only method you need to implement is `parse_row`.

```python
from garf.core.parsers import BaseParser

class MyParser(BaseParser):

  def parse_row(row):
    # Your parsing logic here
```

## Use with ApiReportFetcher

Once your Parser class is defined, you can use with built-in `ApiReportFetcher`.

```python
from garf.core import ApiReportFetcher

report_fetcher = ApiReportFetcher(api_client, parser=MyParser)
```
!!! note
    [Learn more](../usage/fetcher.md) about using `ApiReportFetcher`.
