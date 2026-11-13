# garf MCP - Model Context Protocol server for garf

`garf-executors` includes a [Model Context Protocol (MCP)](https://modelcontextprotocol.io/) server that exposes `garf` resources and tools to AI assistants and MCP-compatible clients (such as Gemini CLI, Antigravity, Claude Desktop, and Cursor).

## Installation

/// tab | pip
```bash
pip install garf-executors[mcp]
```
///

/// tab | uv
```bash
uv pip install garf-executors[mcp]
```
///

!!! note
    Install any [report fetchers](../fetchers/overview.md) (such as `garf-google-ads`, `garf-youtube-data-api`, etc.) and [writers](writers.md) you want to use in the same Python environment where the MCP server runs.

## Starting the Server

You can start the `garf` MCP server using the `grf mcp` CLI command or by running the module directly.

/// tab | cli (stdio)
```bash
grf mcp
```
///

/// tab | cli (http)
```bash
grf mcp --transport http --host 0.0.0.0 --port 8000
```
///

/// tab | Python module
```bash
python -m garf.executors.entrypoints.mcp_server --transport stdio
```
///

/// tab | Docker
```bash
docker run -p 8000:8000 ghcr.io/google/garf:latest \
  grf mcp --transport http --port 8000
```
///

### CLI Options

* `--transport` - Transport protocol to use: `stdio` (default), `http`, `sse`, or `streamable-http`.
* `--host` - Host address to bind when using HTTP-based transports (`0.0.0.0` by default).
* `--port` / `-p` - Port to listen on when using HTTP-based transports (`8000` by default).

### Environment Variables

* `GARF_ALLOWED_FOLDERS` - Comma-separated list of local directories where file-based writers (`csv`, `json`, etc.) are allowed to write files (e.g. `GARF_ALLOWED_FOLDERS=/tmp/garf,/data/reports`).
* `GARF_CACHE_LOCATION` - Directory path to enable query caching when `enable_cache` is set.

## Client Configuration

To connect an MCP client (such as Gemini CLI, Antigravity, Claude Desktop, or Cursor) to `garf`, add `garf` to your client's `mcpServers` configuration:

/// tab | stdio
```json
{
  "mcpServers": {
    "garf": {
      "command": "grf",
      "args": ["mcp"],
      "env": {
        "GARF_ALLOWED_FOLDERS": "/tmp/garf"
      }
    }
  }
}
```
///

/// tab | http
```json
{
  "mcpServers": {
    "garf": {
      "url": "http://localhost:8000/mcp"
    }
  }
}
```
///

## Available Resources

The MCP server exposes read-only resources for inspecting the running `garf` environment:

| Resource URI | Name | Description |
| :--- | :--- | :--- |
| `resource://version` | `version` | Returns the version of the `garf-executors` library. |
| `resource://info` | `info` | Returns the versions of installed core libraries (`executors`, `core`, `io`). |
| `resource://fetchers` | `fetchers` | Lists all installed API report fetchers and their versions (e.g. `google-ads`, `youtube-data-api`, `rest`, `fake`). |
| `resource://executors` | `executors` | Lists all available executors (e.g. `api`, `bq`, `sqldb`, `duckdb`, `opensearch`, `elasticsearch`). |

## Available Tools

### `execute`

Executes a single `garf` query from inline `query` text or a `query_path`.

**Parameters:**

* `source` (required): API source / fetcher alias (e.g. `fake`, `rest`, `google-ads`, `bq`, `sqldb`, `duckdb`).
* `query`: Inline query string to execute.
* `query_path`: Local or remote path to a query file (if `query` is not provided).
* `title`: Optional name for the query (used as the output destination name when writing).
* `context`: Optional execution context:
    * `fetcher_parameters`: Key-value parameters for the report fetcher.
    * `query_parameters`: `macro` and `template` substitutions.
    * `writer`: Writer alias or list of writer aliases (e.g. `console`, `csv`, `json`, `bq`, `sqldb`).
    * `writer_parameters`: Key-value parameters for the writer(s) (e.g. `destination_folder`).
* `enable_cache`: Whether to cache the report (`false` by default).
* `cache_ttl_seconds`: Cache TTL in seconds (`3600` by default).
* `simulate`: Whether to simulate API response (`false` by default).

!!! tip
    * **Returning data directly to the MCP client**: Omit `context.writer` (leave it `null`). The tool will return the fetched rows directly as JSON in `results` and `full_results`.
    * **Writing or printing results**: Set `context.writer` (for example, `"console"` to print or `"csv"` to save to disk). The tool will execute the writer and return the writer confirmation string (e.g. `["[Console] - None"]` or `["[CSV] - at /tmp/test.csv"]`).

#### Examples

/// tab | Return rows directly
```json
{
  "source": "fake",
  "query": "SELECT dimension.string AS name, metric.int AS clicks FROM fake LIMIT 2"
}
```
///

/// tab | Print to console
```json
{
  "source": "fake",
  "query": "SELECT dimension.string AS name FROM fake LIMIT 5",
  "context": {
    "writer": "console"
  }
}
```
///

/// tab | Write to CSV with parameters
```json
{
  "source": "fake",
  "title": "sample_report",
  "query": "SELECT dimension.string AS name, metric.int AS clicks FROM fake",
  "context": {
    "fetcher_parameters": {
      "n_rows": 10
    },
    "writer": "csv",
    "writer_parameters": {
      "destination_folder": "/tmp/garf"
    }
  }
}
```
///

### `execute_batch`

Executes multiple queries in parallel for a shared `source` and `context`.

**Parameters:**

* `source` (required): API source / fetcher alias.
* `batch` (required): Mapping of `query_title` to `query_text`.
* `context`: Optional execution context (`fetcher_parameters`, `query_parameters`, `writer`, `writer_parameters`).
* `enable_cache`: Whether to cache the reports (`false` by default).
* `cache_ttl_seconds`: Cache TTL in seconds (`3600` by default).
* `simulate`: Whether to simulate API responses (`false` by default).

#### Example

```json
{
  "source": "fake",
  "batch": {
    "names": "SELECT dimension.string AS name FROM fake LIMIT 2",
    "metrics": "SELECT metric.int AS clicks FROM fake LIMIT 2"
  },
  "context": {
    "fetcher_parameters": {
      "n_rows": 2
    }
  }
}
```

### `execute_workflow`

Runs a [garf workflow](workflows.md) to completion.

**Parameters:**

* `workflow_path` (required): Local or remote path to the workflow YAML file.
* `config_path`: Optional local or remote path to a [config YAML file](configs.md).
* `selected_aliases`: Optional list of workflow step aliases to execute.
* `skipped_aliases`: Optional list of workflow step aliases to skip.
* `simulate`: Whether to simulate API responses (`false` by default).

#### Example

```json
{
  "workflow_path": "path/to/workflow.yaml",
  "selected_aliases": ["ingest_ads"]
}
```
