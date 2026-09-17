# Rust SDK for garf server

## CLI

* Execute query

```bash
cargo run --bin grf execute path/to/query.sql
```
* Execute workflow

```bash
cargo run --bin grf workflow run path/to/workflow.yaml
```
* Get server info

```bash
cargo run --bin grf server info
```

## Examples

[examples](examples/) folder contains several examples of using garf Rust SDK
in your projects:

* Run query from text (`execute_query`)
* Run workflow from inline definition (`execute_workflow_inline`) and file (`execute_workflow_file`)
* Run batch of queries (`execute_batch`)
* Get results back to rust for printing to console (`fetch`)
* Calling helper functions (i.e. get available fetchers) (`helpers`)

```bash
cargo run --example <EXAMPLE_NAME>
```
