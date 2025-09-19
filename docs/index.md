# garf

## What is garf?

`garf` is a framework for building various connectors to reporting API that provides
users with a SQL-like interface to specify what needs to be extracted from the API.

It allows you to define SQL-like queries alongside aliases and custom extractors
and specify where the results of such query should be stored.
Based on a query `garf` builds the correct request to a reporting API, parses response
and transform it into a structure suitable for writing data.

## Key features


* SQL-like syntax to interact with reporting APIs
* Built-in support for writing data into various local / remote storage
* Available as library, CLI, FastAPI endpoint
* Easily extendable to support various APIs


## Installation

/// tab | pip
```bash
pip install garf-executors
```
///

/// tab | uv
```bash
uv add garf-executors
```
///


## Usage

```bash
garf /path/to/queries \
  --source youtube --source.channel=MY_CHANNEL_ID \
  --output csv
```
