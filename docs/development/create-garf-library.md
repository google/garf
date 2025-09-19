# How to create your own garf-based library


In order to create your own library follow the steps.

## Setup project
* Create a folder `<YOUR-LIBRARY>` folder with a subfolder `garf_<YOUR_LIBRARY>_api` name.

* Create `pyproject.toml` of the following structure:

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
requires-python = ">=3.9"
description = "Garf implementation for <YOUR API>"
readme = "README.md"
classifiers = [
  "Development Status :: 4 - Beta",
  "Programming Language :: Python"
]

[project.entry-points.garf]
<YOUR_API> = "your_library.report_fetcher"
```

!!! important

    Ensure that you register your custom report fetcher as an entrypoint for `garf`:

    ```toml
    [project.entry-points.garf]
    your-api = "your_library.report_fetcher"
    ```

## Implement classes

Go to `garf_<YOUR_LIBRARY>_api` folder and create `report_fetcher.py` file.

### ApiClient

ApiClient is responsible to getting data from an API based on a query.

It's up to you how to implement a request to an API given fields, dimensions, resources, filters and sorts you have.

* Create `<YOUR_LIBRARY>ApiClient` class:

```python
from garf_core import api_clients, query_editor


class MyLibraryApiClient(api_clients.BaseClient):

  def get_response(
    request: query_editor.BaseQueryElements,
    **kwargs: str
  ) -> api_clients.GarfApiResponse:
    results = ... # get results from your API somehow
    return api_clients.GarfApiResponse(results=results)
```

### ReportFetcher

ReportFetcher is initialized based on ApiClient and bundles together query
and API response parsers as well as built-in queries associated with a concrete API .

* Create `<YOUR_LIBRARY>ReportFetcher` class:

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


## Install

To test your project install is as an editable package.
```bash
# launch from the <YOUR-LIBRARY> folder
pip install -e .
```

!!! note
    If you thing others will benefit from your package you can now upload your project to pypi.

## Run

Once you installed the package you can run it with `garf` utility:

```bash
garf query.sql --source YOUR_API
```

!!!note
    Refer to [instructions](../libs/garf_executors/README.md#usage) for fetching data from your api via `garf` CLI tool.
