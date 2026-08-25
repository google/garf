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
