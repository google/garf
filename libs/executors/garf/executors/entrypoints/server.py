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
import pydantic
import typer
import uvicorn
import yaml
from garf.executors import exceptions, setup
from garf.executors.entrypoints import utils
from garf.executors.entrypoints.tracer import (
  initialize_logger,
  initialize_meter,
  initialize_tracer,
)
from garf.executors.workflows import workflow, workflow_runner
from garf.io import reader
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.logging import LoggingInstrumentor
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing_extensions import Annotated

OTEL_SERVICE_NAME = 'garf'
LoggingInstrumentor().instrument(set_logging_format=False)

initialize_tracer()
meter = initialize_meter()

logger = utils.init_logging(
  loglevel='INFO', logger_type='local', name=OTEL_SERVICE_NAME
)
logger.addHandler(initialize_logger())

app = fastapi.FastAPI(
  title='Garf API',
  version=garf.executors.__version__,
  description='Fetches data from APIs and saves it anywhere',
)
FastAPIInstrumentor.instrument_app(app)
typer_app = typer.Typer()


class GarfSettings(BaseSettings):
  """Specifies environmental variables for garf.

  Ensure that mandatory variables are exposed via
  export ENV_VARIABLE_NAME=VALUE.

  Attributes:
    loglevel: Level of logging.
    log_name: Name of log.
    logger_type: Type of logger.
  """

  model_config = SettingsConfigDict(env_prefix='garf_')

  loglevel: str = 'INFO'
  log_name: str = 'garf'
  logger_type: str = 'local'
  enable_telemetry: bool = False
  metrics_to_otel: bool = False
  logs_to_otel: bool = False


class GarfDependencies:
  def __init__(self) -> None:
    """Initializes GarfDependencies."""
    settings = GarfSettings()


class ApiExecutorRequest(pydantic.BaseModel):
  """Request for executing a query.

  Attributes:
    source: Type of API to interact with.
    title: Name of the query used as an output for writing.
    query: Query to execute.
    query_path: Local or remote path to query.
    context: Execution context.
  """

  source: str
  title: Optional[str] = None
  query: Optional[str] = None
  query_path: Optional[Union[str, list[str]]] = None
  context: garf.executors.execution_context.ExecutionContext

  @pydantic.model_validator(mode='after')
  def check_query_specified(self):
    if not self.query_path and not self.query:
      raise exceptions.GarfExecutorError(
        'Missing one of required parameters: query, query_path'
      )
    return self

  def model_post_init(self, __context__) -> None:
    if self.query_path and isinstance(self.query_path, str):
      self.query = reader.FileReader().read(self.query_path)
    if not self.title:
      self.title = str(self.query_path)


class ApiExecutorBatchRequest(pydantic.BaseModel):
  """Request for executing multiple queries.

  Attributes:
    source: Type of API to interact with.
    batch: Mapping between query_title and its text.
    context: Execution context.
  """

  source: str
  batch: dict[str, str]
  context: garf.executors.execution_context.ExecutionContext


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


@app.get('/api/fetchers')
async def get_fetchers(
  dependencies: Annotated[GarfDependencies, fastapi.Depends(GarfDependencies)],
) -> list[str]:
  """Shows all available API sources."""
  return list(garf.executors.fetchers.find_fetchers())


@app.post('/api/execute')
def execute(
  request: ApiExecutorRequest,
  dependencies: Annotated[GarfDependencies, fastapi.Depends(GarfDependencies)],
) -> ApiExecutorResponse:
  query_executor = setup.setup_executor(
    request.source, request.context.fetcher_parameters
  )
  result = query_executor.execute(request.query, request.title, request.context)
  if isinstance(result, garf.core.GarfReport):
    result = result.to_list('dict')
  else:
    result = [result]
  return ApiExecutorResponse(results=result)


@app.post('/api/execute:batch')
def execute_batch(
  request: ApiExecutorBatchRequest,
  dependencies: Annotated[GarfDependencies, fastapi.Depends(GarfDependencies)],
) -> ApiExecutorResponse:
  query_executor = setup.setup_executor(
    request.source, request.context.fetcher_parameters
  )
  results = query_executor.execute_batch(request.batch, request.context)
  return ApiExecutorResponse(results=results)


@app.post('/api/execute:workflow')
async def execute_workflow(
  dependencies: Annotated[GarfDependencies, fastapi.Depends(GarfDependencies)],
  workflow_file: Optional[fastapi.UploadFile] = fastapi.File(None),
  enable_cache: bool = False,
  cache_ttl_seconds: int = 3600,
  selected_aliases: Optional[list[str]] = None,
  skipped_aliases: Optional[list[str]] = None,
) -> list[str]:
  content = await workflow_file.read()
  workflow_data = yaml.safe_load(content.decode('utf-8'))
  execution_workflow = workflow.Workflow(**workflow_data)
  return workflow_runner.WorkflowRunner(
    execution_workflow=execution_workflow
  ).run(
    enable_cache=enable_cache,
    cache_ttl_seconds=cache_ttl_seconds,
    selected_aliases=selected_aliases,
    skipped_aliases=skipped_aliases,
  )


@typer_app.command()
def main(
  host: Annotated[
    str, typer.Option(help='Host to start the server')
  ] = '0.0.0.0',
  port: Annotated[int, typer.Option(help='Port to start the server')] = 8000,
):
  uvicorn.run(app, host=host, port=port, log_config=None)


if __name__ == '__main__':
  typer_app()
