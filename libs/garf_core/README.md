# garf-core - Unified approach for interacting with reporting APIs.

[![PyPI](https://img.shields.io/pypi/v/garf-core?logo=pypi&logoColor=white&style=flat-square)](https://pypi.org/project/garf-core)
[![Downloads PyPI](https://img.shields.io/pypi/dw/garf-core?logo=pypi)](https://pypi.org/project/garf-core/)


`garf-core` contains the base abstractions are used by an implementation for a concrete reporting API.

These abstractions are designed to be as modular and simple as possible:

* `BaseApiClient` - an interface for connecting to APIs.
* `BaseQuery` - encapsulates SQL-like request.
* `QuerySpecification` - parsed SQL-query into various elements.
* `BaseParser` - an interface to parse results from the API. Have a couple of default implementations:
    * `ListParser` - returns results from API as a raw list.
    * `DictParser` - returns results from API as a formatted dict.
        * `NumericDictParser` - returns results from API as a formatted dict with converted numeric values.
* `GarfReport` - contains data from API in a format that is easy to write and interact with.
* `ApiReportFetcher` - responsible for fetching and parsing data from reporting API.

## Installation

`pip install garf-core`
