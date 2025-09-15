# Example queries for `garf-knowledge-graph-api`

To execute the queries you may run them in Python (check [Usage](../README.md#usage))
or use `garf-executors` package (install with `pip install garf-executors`).

## Videos
* [entity](entity.sql) - Performs entities search based on a query
  ```
  garf entity.sql \
    --source knowledge-graph-api --output console \
    --source.query="<YOUR_QUERY_HERE>"
  ```
* [ids](ids.sql) - Gets information on knowledge ids
  ```
  garf ids.sql \
    --source knowledge-graph-api --output console \
    --source.ids=<KG_ID>
  ```
