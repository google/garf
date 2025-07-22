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

import fastapi
import pydantic
import uvicorn

import garf_executors
from garf_executors import exceptions
from garf_io import reader


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
  title: str | None = None
  query: str | None = None
  query_path: str | None = None
  context: garf_executors.api_executor.ApiExecutionContext

  @pydantic.model_validator(mode='after')
  def check_query_specified(self):
    if not self.query_path and not self.query:
      raise exceptions.GarfExecutorError(
        'Missing one of required parameters: query, query_path'
      )
    return self

  def model_post_init(self, __context__) -> None:
    if self.query_path:
      self.query = reader.FileReader().read(self.query_path)
    if not self.title:
      self.title = str(self.query_path)


router = fastapi.APIRouter(prefix='/api')


@router.post('/execute')
async def execute(request: ApiExecutorRequest) -> dict[str, str]:
  if not (concrete_api_fetcher := garf_executors.FETCHERS.get(request.source)):
    raise exceptions.GarfExecutorError(
      f'Source {request.source} is not available.'
    )

  query_executor = garf_executors.api_executor.ApiQueryExecutor(
    concrete_api_fetcher(**request.context.fetcher_parameters)
  )

  result = query_executor.execute(request.query, request.title, request.context)

  return fastapi.responses.JSONResponse(
    content=fastapi.encoders.jsonable_encoder({'result': result})
  )


if __name__ == '__main__':
  app = fastapi.FastAPI()
  app.include_router(router)
  uvicorn.run(app)
