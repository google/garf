# How to create your own garf-based library


In order to create your own library follow the steps below:

1. Create a folder `<YOUR-LIBRARY>` folder with a subfolder `garf_<YOUR_LIBRARY>_api` name.

2. Create `pyproject.toml` of the following structure:

```toml
[build-system]
requires = ["setuptools >= 61.0"]
build-backend = "setuptools.build_meta"

[project]
name = "garf-<YOUR_API>"
dependencies = [
  "garf-core",
  "garf-io",
]
version = "0.0.1"
license = {text = "Apache 2.0"}
requires-python = ">=3.8"
description = "Garf implementation for <YOUR API>"
readme = "README.md"
classifiers = [
  "Development Status :: 4 - Beta",
  "Programming Language :: Python"
]

[project.entry-points.garf]
<YOUR_API> = "your_library.report_fetcher"
```


Ensure that you register your custom report fetcher as an entrypoint for `garf`:

```toml
[project.entry-points.garf]
your-api = "your_library.report_fetcher"
```

3. Go to `garf_<YOUR_LIBRARY>_api` folder and create `report_fetcher.py` file.

4. Create `<YOUR_LIBRARY>ApiClient` class:

```python
from garf_core import api_clients, query_editor


class MyLibraryApiClient(api_clients.BaseClient):

  def get_response(
    request: query_editor.BaseQueryElements
  ) -> api_clients.GarfApiResponse:
    results = ... # get results from your API somehow
    return api_clients.GarfApiResponse(results=results)
```

5. Create `<YOUR_LIBRARY>ReportFetcher` class:

```python
from garf_core import report_fetcher


class MyLibraryApiReportFetcher(report_fetcher.ApiReportFetcher):
  def __init__(
    self,
    api_client: MyLibraryApiClient = MyLibraryApiClient(),
    **kwargs: str
    ) -> None:
    super().__init__(api_client, **kwargs)
```


6. You can now upload your project to pypi or install as an editable:

```
# launch from the <YOUR-LIBRARY> folder
pip install -e .
```

7. Refer to [instructions](../libs/garf_executors/README.md#usage) for fetching data from your api via `garf` CLI tool.
