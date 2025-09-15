# garf-core - Unified approach for interacting with reporting APIs.

[![PyPI](https://img.shields.io/pypi/v/garf-core?logo=pypi&logoColor=white&style=flat-square)](https://pypi.org/project/garf-core)
[![Downloads PyPI](https://img.shields.io/pypi/dw/garf-core?logo=pypi)](https://pypi.org/project/garf-core/)


`garf-core` contains the base abstractions are used by an implementation for a concrete reporting API.

These abstractions are designed to be as modular and simple as possible:

* `BaseApiClient` - an interface for connecting to APIs. Check [default implementations](docs/builtin-functionality.md#apiclients)
* `BaseParser` - an interface to parse results from the API. Check [default implementations](docs/builtin-functionality.md#parsers)
* `ApiReportFetcher` - responsible for fetching and parsing data from reporting API. [Default implementations](docs/builtin-functionality.md#apireportfetchers)

* `QuerySpecification` - parsed SQL-query into various elements.
* `BaseQuery` - protocol for all class based queries.
* `GarfReport` - contains data from API in a format that is easy to write and interact with.

## Installation

`pip install garf-core`
