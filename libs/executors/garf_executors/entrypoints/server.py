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

from typing import Optional, Union

import fastapi
import pydantic
import uvicorn
from garf_io import reader
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor

import garf_executors
from garf_executors import exceptions
from garf_executors.entrypoints.tracer import initialize_tracer

initialize_tracer()
app = fastapi.FastAPI()
FastAPIInstrumentor.instrument_app(app)


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
  context: garf_executors.api_executor.ApiExecutionContext

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
  return garf_executors.__version__


@app.get('/api/fetchers')
async def get_fetchers() -> list[str]:
  """Shows all available API sources."""
  return list(garf_executors.fetchers.find_fetchers())


@app.post('/api/execute')
async def execute(request: ApiExecutorRequest) -> ApiExecutorResponse:
  query_executor = garf_executors.setup_executor(
    request.source, request.context.fetcher_parameters
  )
  result = query_executor.execute(request.query, request.title, request.context)
  return ApiExecutorResponse(results=[result])


@app.post('/api/execute:batch')
def execute_batch(request: ApiExecutorRequest) -> ApiExecutorResponse:
  query_executor = garf_executors.setup_executor(
    request.source, request.context.fetcher_parameters
  )
  reader_client = reader.FileReader()
  batch = {query: reader_client.read(query) for query in request.query_path}
  results = query_executor.execute_batch(batch, request.context)
  return ApiExecutorResponse(results=results)


if __name__ == '__main__':
  uvicorn.run(app)
