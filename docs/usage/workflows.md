# Workflows

Workflows in `garf` allow you to orchestrate complex data fetching and processing pipelines.
Instead of running individual queries, you can define a sequence of steps,
where each step interacts with a specific data source (fetcher) and writes to a destination.

## Configuration

Workflows are defined in YAML files. The core structure consists of a list of
`steps`, where each step defines what data to fetch and where to save it.

### Workflow Step Structure

```yaml
steps:
  - alias: step_name
    fetcher: source_name
    writer: destination
    writer_parameters:
      key: value
    fetcher_parameters:
      key: value
    query_parameters:
      macro:
        key: value
      template:
        key: value
    queries:
      - folder: path/to/queries/
      - path: path/to/query.sql
      - query:
          text: "SELECT 1"
          title: "simple_query"
    parallel_threshold: 10
```

### Components

*   **fetcher**: The source of data. Check [available fetchers](../fetchers/overview.md).
*   **fetcher_parameters**: Key value pairs used to fine-tune fetching process.
*   **alias**: A unique identifier for the step. Useful for logging and [selective execution](#selective-execution).
*   **writer**: Where the data should be saved. Check [available writers](writers.md).
*   **writer_parameters**: Key value pairs used to fine-tune writing process.
*   **query_parameters**: (Optional) Parameters for dynamically changing query text.
*   **queries**: A list of queries to execute in this step. Can be:
    *   `folder`: Recursively finds all `.sql` files in the directory.
    *   `path`: Path to a specific query file.
    *   `query`: Inline query definition with `text` and `title`.
*   **parallel_threshold**: Custom threshold of parallel query execution for a given step.


### Common Parameters

You can use YAML anchors and aliases to avoid repetition,
which is especially useful for sharing configuration between steps.

```yaml
# Define shared configuration
default_bq: &bq_defaults
  writer: bq
  writer_parameters:
    project: my-project
    dataset: my_dataset

steps:
  - alias: step_1
    fetcher: google-ads
    <<: *bq_defaults
    queries: ...

  - alias: step_2
    fetcher: google-ads
    <<: *bq_defaults
    queries: ...
```

## Usage

/// tab | cli
```bash
garf -w workflow.yaml
```

///

/// tab | Python
```python
from garf.executors.workflows import workflow_runner

runner = workflow_runner.WorkflowRunner.from_file("path/to/workflow.yaml")
runner.run()
```
///

/// tab | server

!!!note
    Ensure that API endpoint for `garf` is running.
    ```bash
    python -m garf.executors.entrypoints.server
    ```

```bash
curl -X 'POST' \
  'http://127.0.0.1:8000/api/execute:workflow?workflow_file=workflow.yaml' \
  -H 'accept: application/json' \
  -H 'Content-Type: application/json' \
  -d ''
```
///

## Customization

### Include/Exclude Steps

Instead of running the whole workflow you can selected or omit certain steps.

/// tab | cli
```bash
garf -w workflow.yaml --workflow-include alias_1 --workflow-exclude alias_3
```

///

/// tab | Python
```python
from garf.executors.workflows import workflow_runner

runner = workflow_runner.WorkflowRunner.from_file("path/to/workflow.yaml")
runner.run(selected_aliases=['alias_1'], skipped_aliases=['alias_3'])
```
///

/// tab | server

!!!note
    Ensure that API endpoint for `garf` is running.
    ```bash
    python -m garf.executors.entrypoints.server
    ```

```bash
curl -X 'POST' \
  'http://127.0.0.1:8000/api/execute:workflow?workflow_file=workflow.yaml' \
  -H 'accept: application/json' \
  -H 'Content-Type: application/json' \
  -d '{
  "selected_aliases": [
    "alias_1"
  ],
  "skipped_aliases": [
    "alias_3"
  ]
}'
```
///

## Example

Here is a comprehensive example showing a multi-step pipeline:

```yaml
bq_project: &bq_project "my-gcp-project"
bq_dataset: &bq_dataset "marketing_data"

steps:
  # Step 1: Fetch data from Google Ads
  - alias: ingest_ads
    fetcher: google-ads
    fetcher_parameters:
      account: "123-456-7890"
    writer: bq
    writer_parameters:
      project: *bq_project
      dataset: *bq_dataset
    queries:
      - path: queries/ads_reporting/roas.sql

  # Step 2: Filter data in BigQuery and save to CSV
  - alias: transform_data
    fetcher: bq
    fetcher_parameters:
      project: *bq_project
    queries:
      - query:
          title: "filtered_roas"
          text: "SELECT roas FROM `{dataset}.roas` WHERE roas > 1"
    query_parameters:
      macro:
        dataset: *bq_dataset
    writer: csv
```
