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

import os
from typing import Optional, Union

import fastapi
import garf.executors
import pydantic
import typer
import uvicorn
from garf.executors import exceptions, setup
from garf.executors.entrypoints import utils
from garf.executors.entrypoints.tracer import (
  initialize_logger,
  initialize_meter,
  initialize_tracer,
)
from garf.executors.workflows import workflow_runner
from garf.io import reader
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing_extensions import Annotated

if os.getenv('GARF_ENABLE_TELEMETRY') or os.getenv('GARF_TRACES_TO_OTEL'):
  initialize_tracer()

app = fastapi.FastAPI()
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
    logger = utils.init_logging(
      loglevel=settings.loglevel,
      logger_type=settings.logger_type,
      name=settings.log_name,
    )
    if settings.enable_telemetry or settings.metrics_to_otel:
      initialize_meter()
    if settings.enable_telemetry or settings.logs_to_otel:
      logger.addHandler(initialize_logger())
    self.logger = logger


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
  context: garf.executors.api_executor.ApiExecutionContext

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


class ApiExecutorResponse(pydantic.BaseModel):
  """Response after executing a query.

  Attributes:
    results: Results of query execution.
  """

  results: list[str]


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
  return ApiExecutorResponse(results=[result])


@app.post('/api/execute:batch')
def execute_batch(
  request: ApiExecutorRequest,
  dependencies: Annotated[GarfDependencies, fastapi.Depends(GarfDependencies)],
) -> ApiExecutorResponse:
  query_executor = setup.setup_executor(
    request.source, request.context.fetcher_parameters
  )
  reader_client = reader.FileReader()
  batch = {query: reader_client.read(query) for query in request.query_path}
  results = query_executor.execute_batch(batch, request.context)
  return ApiExecutorResponse(results=results)


@app.post('/api/execute:workflow')
def execute_workflow(
  workflow_file: str,
  dependencies: Annotated[GarfDependencies, fastapi.Depends(GarfDependencies)],
  enable_cache: bool = False,
  cache_ttl_seconds: int = 3600,
  selected_aliases: Optional[list[str]] = None,
  skipped_aliases: Optional[list[str]] = None,
) -> list[str]:
  return workflow_runner.WorkflowRunner.from_file(workflow_file).run(
    enable_cache=enable_cache,
    cache_ttl_seconds=cache_ttl_seconds,
    selected_aliases=selected_aliases,
    skipped_aliases=skipped_aliases,
  )


@typer_app.command()
def main(
  port: Annotated[int, typer.Option(help='Port to start the server')] = 8000,
):
  uvicorn.run(app, port=port)


if __name__ == '__main__':
  typer_app()
