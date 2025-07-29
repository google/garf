# garf

## What is garf?

`garf` is a framework for building various connectors to reporting API that provides
users with a SQL-like interface to specify what needs to be extracted from the API.

The framework allows you to define SQL-like queries alongside aliases and custom extractors and specify where the results of such query should be stored.
Based on such a query the library constructs the correct query to a reporting API of your choice, automatically extract all necessary fields from API schema
and transform them into a structure suitable for writing data.

## Key features

* Uses SQL-like syntax to interact with reporting APIs
* Built-in support for writing data into various local / remote storage
* Available as library, CLI, FastAPI endpoint
* Easily extendable to support various APIs


## Installation
```python
pip install garf-executors
```

`garf` consist of several core libraries:

* [`garf-core`](https://github.com/google/garf/tree/main/libs/garf_core) - exposes interfaces and core classes such as `GarfReport`.
* [`garf-io`](https://github.com/google/garf/tree/main/libs/garf_io) - handles reading queries and writing `GarfReport` to various local/remote storages.
* [`garf-executors`](https://github.com/google/garf/tree/main/libs/garf_executors) - responsible for orchestrating process of fetching from API and storing data in a storage.

[`garf-community`](https://github.com/google/garf/tree/main/libs/garf_community) folder contains concrete implementation of the framework for various APIs.
