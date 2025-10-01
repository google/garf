# Overview

[![PyPI](https://img.shields.io/pypi/v/garf-core?logo=pypi&logoColor=white&style=flat-square)](https://pypi.org/project/garf-core)
[![Downloads PyPI](https://img.shields.io/pypi/dw/garf-core?logo=pypi)](https://pypi.org/project/garf-core/)

`garf-core` contains the base abstractions are used by an implementation for a concrete reporting API.

These abstractions are designed to be as modular and simple as possible:

* [`BaseApiClient`](api-client.md) - an interface for connecting to APIs.
* [`BaseParser`](parsers.md) - an interface to parse results from the API.
* [`ApiReportFetcher`](fetcher.md) - responsible for fetching and parsing data from reporting API.
* [`GarfReport`](reports.md) - contains data from API in a format that is easy to write and interact with.
* `QuerySpecification` - parsed SQL-query into various elements.
* [`BaseQuery`](queries.md#queries-as-python-objects) - protocol for all class based queries.

## Installation

/// tab | pip
```bash
pip install garf-core
```
///

/// tab | uv
```bash
uv pip install garf-core
```
///
