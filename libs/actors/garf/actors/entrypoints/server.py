# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# pylint: disable=C0330, g-bad-import-order, g-multiple-import


import time
from contextlib import asynccontextmanager

import fastapi
import garf.executors
import typer
import uvicorn
from garf.actors import actor, runner, telemetry, version
from garf.executors.entrypoints import utils
from garf.executors.entrypoints.tracer import (
  initialize_logger,
  initialize_meter,
  initialize_tracer,
)
from garf.executors.workflows import workflow
from opentelemetry import _logs, metrics, trace
from typing_extensions import Annotated

OTEL_SERVICE_NAME = 'garf-actors'

server_start_time = time.time()
tracer = initialize_tracer()
meter = initialize_meter()
telemetry_logger = initialize_logger()
trace.set_tracer_provider(tracer)
metrics.set_meter_provider(meter)
_logs.set_logger_provider(telemetry_logger)


def _get_server_info(options):
  yield metrics.Observation(
    value=1,
    attributes={
      'version_actors': version.__version__,
      'version_executors': garf.executors.version.__version__,
      'version_core': garf.executors.version.core_version,
      'version_io': garf.executors.version.io_version,
      'server_type': 'http',
    },
  )


actor_info = telemetry.meter.create_observable_gauge(
  'garf_actor_info',
  callbacks=[_get_server_info],
  unit='',
  description='Build info of garf actor',
)

logger = utils.init_logging(
  loglevel='INFO', logger_type='local', name=OTEL_SERVICE_NAME
)
logger.addHandler(telemetry_logger)

available_actors = {}
available_actor_classes = {}
available_workflows = {}


@asynccontextmanager
async def lifespan(app: fastapi.FastAPI):
  available_workflows.update(actor.load_workflows())
  available_actors.update(actor.load_actors())
  for actors in available_actors.values():
    for actor_class in actors:
      available_actor_classes[actor_class.__name__] = actor_class
  yield
  available_actors.clear()
  available_workflows.clear()
  available_actor_classes.clear()


typer_app = typer.Typer()
app = fastapi.FastAPI(
  title='Garf Actors',
  version=version.__version__,
  lifespan=lifespan,
)


@app.get('/api/version')
def actors_version():
  return version.__version__


@app.get('/api/{source}/actors')
async def get_actors(source: str) -> dict[str, str]:
  """Shows all available API actors for a source."""
  if available_source := available_actors.get(source):
    return {actor.__name__: actor.__doc__ or '' for actor in available_source}
  return {}


@app.get('/api/sources')
async def get_sources() -> list[str]:
  """Shows all available actor sources."""
  return available_actors.keys()


@app.get('/api/{source}/workflows')
def source_workflows(source: str) -> dict[str, str]:
  """Shows all available workflows for a particular source."""
  if source_workflows := available_workflows.get(source):
    return {
      name: workflow.metadata.description.strip()
      if workflow.metadata.description
      else ''
      for name, workflow in source_workflows.items()
    }
  return {}


@app.get('/api/{source}/workflows/{name}')
def workflow_info(source: str, name: str) -> workflow.Workflow | None:
  """Shows a particular workflow."""
  if actor_workflow := available_workflows.get(source, {}).get(name):
    return actor_workflow
  return None


@app.post('/api/', response_model=actor.ActionResult)
def interact(request: runner.GarfActorRequest) -> str:
  """Interacts with garf actors."""
  actor_workflow = available_workflows.get(request.input.source, {}).get(
    request.input.name
  )
  concrete_actor = available_actor_classes.get(request.actor)

  return request.play(
    workflow=actor_workflow, actor=concrete_actor() if concrete_actor else None
  )


@typer_app.command()
def main(
  host: Annotated[
    str, typer.Option(help='Host to start the server')
  ] = '0.0.0.0',
  port: Annotated[
    int, typer.Option('--port', '-p', help='Port to start the server')
  ] = 8000,
):
  uvicorn.run(app, host=host, port=port, log_config=None)


if __name__ == '__main__':
  typer_app()
