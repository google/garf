# Overview

While `garf-executors` provides an easy way of getting data from reporting
part of APIs, `garf-actors` allows you to perform action on those APIs, for example:

* Upload new video to YouTube
* Set new campaign budget in Google Ads
* Create new image with Gemini


## Architecture

`garf-actors` works with two core elements:

* Evaluation workflows
* Source specific actors

### Evaluation workflow

Evaluation workflow represents a [garf workflow](#workflows.md) with the final
*evaluation* step. This step combined all the results from the previous steps
and contains `filters` template variable that allowed you to perform conditional
filtering.

```yaml
steps:
  - alias: task
    fetcher: fake
    fetcher_parameters:
      n_rows: 10
    writer:
      - sqldb
    writer_parameters:
      connection_string: sqlite:////tmp/garf-actors.db
    queries:
      - text: |
          SELECT
            dimension.string AS field,
            metric.int AS value
          FROM fake
        title: fake
  - alias: evaluation
    fetcher: sqldb
    fetcher_parameters:
      connection_string: sqlite:////tmp/garf-actors.db
    queries:
      - text: |
          SELECT *
          FROM fake
          WHERE {{filters}}
        title: evaluation
    query_parameters:
      macro_expansion: False
      template:
        filters: "TRUE"
```

### Actor

Actors operate on reports produced by the evaluation step of the workflow.


For example, if the report contains keywords and campaign_ids that need to be
added you can call hypothetical `KeywordAdded` actor that adds them via Google
Ads API.

## Running

`garf-actors` are available only as an HTTP server.

Start the server with the following command:

```bash
python -m garf.actors.entrypoints.server
```

The server is available on at `http://localhost:8000`

Now perform an action

```bash
curl -X POST http://localhost:8000/api/ \
  -d '{
    "rule": "value > 10",
    "input" {
      "source": "fake",
      "workflow_name": "fake"
    },
    "actor": "Faker"
  }'
```


This command will look for `Faker` actor in `fake` namespace and then call
`fake` workflow while providing a custom filter `value > 10`.

## Customizing

While running actor with a built-in workflow might be sufficient for some case
the true power comes from providing custom queries and workflow.

### Input & parameters

Apart from built-in `workflow_name` other types of input can be provided.

#### query

Represents a single query executed via `garf`. Can be a call to an API or DB.

To issue a query specify `"type": "query"` and provide query text in `data` attribute of the request.

```bash
curl -X POST http://localhost:8000/api/ \
  -d '{
    "rule": "value > 10",
    "input" {
      "source": "fake",
      "type": "query",
      "data": "SELECT metric.int AS value FROM fake"
    },
    "actor": "Faker"
  }'
```

#### workflow

When a single query not enough you can use the power of [workflows](#evaluateion-workflow).

To issue a query specify `"type": "workflow"` and provide full workflow definition in `data` attribute of the request.

```bash
curl -X POST http://localhost:8000/api/ \
  -d '{
    "rule": "value > 10",
    "input" {
      "source": "fake",
      "type": "workflow",
      "data":  {
        "steps": [
          {
            "fetcher": "fake",
            "alias": "task",
            "writer": [
              "sqldb",
            ],
            "queries": [
              {
                "text": SELECT metric.int AS value FROM fake,
                 "title": "task"
              },
            ],
          },
          {
            "fetcher": "sqldb",
            "alias": "evaluation",
            "queries": [
              {
                "text": "SELECT * FROM task WHERE {{ filters }}",
                "title": "evaluation",
              },
            ],
            "query_parameters": {
              "template": {
                "filters": "TRUE",
              }
            },
          },
        ]
    },
    "actor": "Faker"
  }'
```

#### workflow_file

If workflow becomes to big to be injected into the request you can use `workflow_file` instead.
To issue a query specify `"type": "workflow_file"` and provide fully qualified path to workflow in `data` attribute of the request.

!!! important
    Workflow file should be accessible to the `garf-actors` server running.
    Alternatively you can provide a remote file (http, gcs, s3, azure, etc.)

```bash
curl -X POST http://localhost:8000/api/ \
  -d '{
    "rule": "value > 10",
    "input" {
      "source": "fake",
      "type": "workflow_file",
      "data": "workflow.yaml"
    },
    "actor": "Faker"
  }'
```

#### context

While queries and workflows specified what need to be fetched, `context` focuses on specifics (which database to use, from which accounts to get data, etc.)

`context` consists of a set of nested dictionaries each one specifies parameters for a particular writer or fetcher.

```bash
curl -X POST http://localhost:8000/api/ \
  -d '{
    "rule": "value > 10",
    "input" {
      "source": "fake",
      "type": "query",
      "data": "SELECT metric.int AS value FROM fake"
      "context": {
        "fake": {
          "n_rows": 20
        },
        "sqldb": {
          "connection_string": "sqlite:////tmp/garf-actors.db"
        }
      }
    },
    "actor": "Faker"
  }'
```

### Rule

`rule` represents a specific kind of filter that applied at the evaluation step before the data is sent to the actor.

Rule is injected as `WHERE` statement and thus can use all the available SQL syntax to perform the filtering.

!!! important
    Elements appearing in `rule` should be found in the query at evaluation
    step.


### Actor & parameters

After all the data has been gathered and filtered `Actor` performs necessary action (adding or removing criteria, sending notification, applying labels). Actor depends on a on a source provided in `input`.

You can customize actor by providing key-value pairs in  `actor_parameters` attribute.

```bash
curl -X POST http://localhost:8000/api/ \
  -d '{
    "rule": "value > 10",
    "input" {
      "source": "fake",
      "type": "query",
      "data": "SELECT metric.int AS value FROM fake"
    },
    "actor": "Faker",
    "actor_parameters": {
      "key": "value"
    }
  }'
```


## Creating your actors & workflows

But the true power comes from creating your own actors and evaluation workflows.

`garf-actors` automatically picks up those given that they are exposed as
entrypoints in Python packages.


```toml
[project.entry-points.garf_actors]
actor-source-name = "path.to.actor"

[project.entry-points.garf_actor_workflows]
actor-source-name = "path.to.workflow.folder"
```

One you created a package, install it in the same environment where `garf-actor`
serve running.

### Actors

To create an actor you need to follow two prerequisites:

* Inherit from  `garf.actors.Actor`
* Implement `act` method which accepts two parameters:
    *  `report` - `garf.core.GarfReport` that contains necessary data to perform
       necessary action.
    * `**kwargs` - to propagate optional parameters
