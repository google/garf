# Overview

Let's use `garf` to query [https://restful-api.dev](https://restful-api.dev) (publicly available API) and save results to BigQuery.

## Installation

/// tab | pip
```
pip install garf-executors
```
///

/// tab | uv
```
uv add garf-executors
```
///

## Create query

[https://restful-api.dev](https://restful-api.dev) has ` https://api.restful-api.dev/objects` endpoint to get list of objects in the following format:

```json
[
   {
      "id": "1",
      "name": "Google Pixel 6 Pro",
      "data": {
         "color": "Cloudy White",
         "capacity": "128 GB"
      }
   },
   {
      "id": "2",
      "name": "Apple iPhone 12 Mini, 256GB, Blue",
      "data": null
   },
   {
      "id": "3",
      "name": "Apple iPhone 12 Pro Max",
      "data": {
         "color": "Cloudy White",
         "capacity GB": 512
      }
   }
]
```

Support we want to get `id`, `name` and `color` of each device.

Let's create a query to get this information.

```sql
SELECT
  id AS device_id,
  name AS device_name,
  data.color AS device_color
FROM objects
```

We can save this query to a local file called `devices.sql`.

```bash
echo "
SELECT
  id AS device_id,
  name AS device_name,
  data.color AS device_color
FROM objects" > devices.sql
```

## Execute query

Since the API we're working with is of REST type we can use `garf`'s built-in `rest` source and provide API address to get data from.

We'll use `garf` CLI tool get the data. The only thing we need to specify is root endpoint where API is located (`https://api.restful-api.dev` in our case).

```bash
garf devices.sql --source rest \
  --source.endpoint=https://api.restful-api.dev \
  --output bq
```

!!! note
    Since we want to write data to BigQuery we specified `bq` output type.
    By default results will be stored in default project (`GOOGLE_CLOUD_PROJECT`) in `garf` dataset under name `devices`.

## Next steps

Congratulations, you executed your first query with `garf`!

Now you can explore various options `garf` provides:

* **How to write queries**: Learn an extensive [SQL syntax](../usage/queries.md) capabilities `garf` supports.
* **How to use garf in your Python projects**: `garf` makes it easy to [fetch data](../usage/fetcher.md) and works with fetched [reports](../usage/reports.md).
* **Supported writers**: Learn where you can [write data](../usage/writers.md) fetched from your APIs.
* **Executors**: Learn how to process multiple queries with [executors](../usage/executors.md).
