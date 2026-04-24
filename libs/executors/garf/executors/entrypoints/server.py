# Copyright 2025 Google LLC
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

"""FastAPI endpoint for executing queries."""

from typing import Any, Optional, Union

import fastapi
import garf.core
import garf.executors
import garf.io
import pydantic
import typer
import uvicorn
import yaml
from garf.executors.entrypoints import tasks, utils
from garf.executors.entrypoints.tracer import (
  initialize_logger,
  initialize_meter,
  initialize_tracer,
)
from garf.executors.workflows import workflow
from opentelemetry import trace
from opentelemetry.instrumentation.celery import CeleryInstrumentor
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.logging import LoggingInstrumentor
from typing_extensions import Annotated

OTEL_SERVICE_NAME = 'garf'
LoggingInstrumentor().instrument(set_logging_format=False)

initialize_tracer()
meter = initialize_meter()

logger = utils.init_logging(
  loglevel='INFO', logger_type='local', name=OTEL_SERVICE_NAME
)
logger.addHandler(initialize_logger())

CeleryInstrumentor().instrument()
app = fastapi.FastAPI(
  title='Garf API',
  version=garf.executors.__version__,
  description='Fetches data from APIs and saves it anywhere',
)
FastAPIInstrumentor.instrument_app(app)
typer_app = typer.Typer()


class ApiExecutorResponse(pydantic.BaseModel):
  """Response after executing a query.

  Attributes:
    results: Results of query execution.
  """

  results: list[Union[str, Any]]


@app.exception_handler(garf.core.exceptions.GarfError)
async def error_handlier(
  request: fastapi.Request, exc: garf.core.exceptions.GarfError
):
  error_mapping = {}

  status_code = error_mapping.get(type(exc), 400)

  return fastapi.responses.JSONResponse(
    status_code=status_code,
    content={
      'error_type': type(exc).__name__,
      'detail': str(exc),
    },
  )


@app.get('/api/version')
async def version() -> str:
  return garf.executors.__version__


@app.get('/api/info')
async def info() -> dict[str, str]:
  """Returns version of installed core libraries."""
  return {
    'executors': garf.executors.__version__,
    'core': garf.core.__version__,
    'io': garf.io.__version__,
  }


@app.get('/api/fetchers')
async def get_fetchers() -> list[str]:
  """Shows all available API sources."""
  return list(garf.executors.fetchers.find_fetchers())


@app.post('/api/execute')
def execute(request: tasks.ApiExecutorRequest) -> ApiExecutorResponse:
  """Executes a single query."""
  result = tasks.execute(request.model_dump())
  return ApiExecutorResponse(results=result)


@app.post('/api/execute:task', status_code=fastapi.status.HTTP_202_ACCEPTED)
def execute_task(request: tasks.ApiExecutorRequest) -> dict[str, str]:
  """Creates a single operation for running garf query."""
  task = tasks.execute.delay(request.model_dump())
  span = trace.get_current_span()
  span.set_attribute('garf.operation.id', task.id)
  return {'operation_id': task.id, 'status': 'PENDING'}


@app.post('/api/execute:batch')
def execute_batch(
  request: tasks.ApiExecutorBatchRequest,
) -> ApiExecutorResponse:
  """Executes multiple queries in parallel."""
  results = tasks.execute_batch(request.model_dump())
  return ApiExecutorResponse(results=results)


@app.post('/api/execute:batch_task')
async def execute_batch_task(
  request: tasks.ApiExecutorBatchRequest,
) -> dict[str, str]:
  """Creates a single operation for running multiple garf queries."""
  task = tasks.execute_batch.delay(request.model_dump())
  span = trace.get_current_span()
  span.set_attribute('garf.operation.id', task.id)
  return {'operation_id': task.id, 'status': 'PENDING'}


@app.post('/api/execute:workflow')
def execute_workflow(
  workflow_file: Optional[fastapi.UploadFile] = fastapi.File(None),
  enable_cache: bool = False,
  cache_ttl_seconds: int = 3600,
  selected_aliases: Optional[list[str]] = None,
  skipped_aliases: Optional[list[str]] = None,
) -> list[str]:
  """Runs garf workflow till completion."""
  content = workflow_file.file.read()
  workflow_data = yaml.safe_load(content.decode('utf-8'))
  execution_workflow = workflow.Workflow(**workflow_data)
  return tasks.execute_workflow(
    execution_workflow=execution_workflow.model_dump(),
    enable_cache=enable_cache,
    cache_ttl_seconds=cache_ttl_seconds,
    selected_aliases=selected_aliases,
    skipped_aliases=skipped_aliases,
  )


@app.post('/api/execute:workflow_task')
async def execute_workflow_task(
  workflow_file: Optional[fastapi.UploadFile] = fastapi.File(None),
  enable_cache: bool = False,
  cache_ttl_seconds: int = 3600,
  selected_aliases: Optional[list[str]] = None,
  skipped_aliases: Optional[list[str]] = None,
) -> dict[str, str]:
  """Creates a single operation for running garf workflow."""
  span = trace.get_current_span()
  content = await workflow_file.read()
  workflow_data = yaml.safe_load(content.decode('utf-8'))
  execution_workflow = workflow.Workflow(**workflow_data)
  task = tasks.execute_workflow.delay(
    execution_workflow=execution_workflow.model_dump(),
    enable_cache=enable_cache,
    cache_ttl_seconds=cache_ttl_seconds,
    selected_aliases=selected_aliases,
    skipped_aliases=skipped_aliases,
  )
  span.set_attribute('garf.operation.id', task.id)
  return {'operation_id': task.id, 'status': 'PENDING'}


@app.get('/api/operations/{operation_id}')
def operation_status(operation_id: str):
  """Gets garf execution status and results."""
  operation = tasks.app.AsyncResult(operation_id)
  return {
    'operation_id': operation_id,
    'status': operation.status,
    'results': operation.result if operation.status == 'SUCCESS' else None,
  }


@app.post('/api/operations/{operation_id}:cancel')
def cancel_operation(operation_id: str):
  """Cancels garf operation."""
  tasks.app.control.revoke(operation_id, terminate=True)
  return {
    'operation_id': operation_id,
    'status': 'CANCELED',
  }


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
