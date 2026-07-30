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


from collections import defaultdict
from contextlib import asynccontextmanager

import fastapi
import typer
import uvicorn
from garf.actors import actor, runner, version
from garf.executors.workflows import workflow
from typing_extensions import Annotated

available_actors = {}
available_workflows = {}


@asynccontextmanager
async def lifespan(app: fastapi.FastAPI):
  available_workflows.update(actor.load_workflows())
  available_actors.update(actor.load_actors())
  yield
  available_actors.clear()
  available_workflows.clear()


typer_app = typer.Typer()
app = fastapi.FastAPI(
  title='Garf Actors',
  version=version.__version__,
  lifespan=lifespan,
)


@app.get('/api/version')
def actors_version():
  return version.__version__


@app.get('/api/actors')
async def get_actors() -> dict[str, list[str]]:
  """Shows all available API actors."""
  return {
    actor_source: [actor.__name__ for actor in actors]
    for actor_source, actors in available_actors.items()
  }


@app.get('/api/workflows')
async def get_workflows() -> dict[str, dict[str, workflow.Workflow]]:
  """Shows all available actor workflows."""
  converted_workflows = defaultdict(dict)
  for workflow_source, workflows in available_workflows.items():
    for workflow_key, workflow_data in workflows.items():
      converted_workflows.update({workflow_key: workflow_data})
  return available_workflows


@app.get('/api/workflow/{source}')
def source_workflows(source: str) -> dict[str, workflow.Workflow]:
  """Shows all available workflows for a particular source."""
  if source_workflows := available_workflows.get(source):
    return source_workflows
  return {}


@app.get('/api/workflow/{source}/{name}')
def workflow_info(source: str, name: str) -> workflow.Workflow:
  """Shows a particular workflow."""
  if actor_workflow := available_workflows.get(source, {}).get(name):
    return actor_workflow
  return {}


@app.post('/api/', response_model=actor.ActionResult)
def play(request: runner.GarfActorRequest) -> str:
  """Interacts with garf actors."""
  return request.play()


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
