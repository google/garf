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


class ApiExecutorRequest(pydantic.BaseModel):
  """Request for executing a query.

  Attributes:
    source: Type of API to interact with.
    query: Query to execute.
    title: Name of the query used as an output for writing.
    context: Execution context.
  """

  source: str
  query: str
  title: str
  context: garf_executors.api_executor.ApiExecutionContext


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

  query_executor.execute(request.query, request.title, request.context)

  return fastapi.responses.JSONResponse(
    content=fastapi.encoders.jsonable_encoder({'result': 'success'})
  )


if __name__ == '__main__':
  app = fastapi.FastAPI()
  app.include_router(router)
  uvicorn.run(app)
