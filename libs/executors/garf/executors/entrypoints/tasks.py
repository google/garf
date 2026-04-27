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
import os
from typing import Optional, Union

import celery
import garf.core
import garf.executors
import pydantic
from garf.executors import exceptions, setup
from garf.executors.entrypoints import utils as garf_utils
from garf.executors.entrypoints.tracer import (
  initialize_logger,
  initialize_meter,
  initialize_tracer,
)
from garf.executors.workflows import workflow, workflow_runner
from garf.io import reader
from opentelemetry.instrumentation.celery import CeleryInstrumentor
from opentelemetry.instrumentation.redis import RedisInstrumentor

redis_url = os.getenv('CELERY_BROKER_URL', 'redis://localhost:6379/0')


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


@celery.signals.worker_process_init.connect(weak=False)
def init_celery_telemetry(*args, **kwargs):
  otel_service_name = 'garf-celery'
  initialize_tracer(otel_service_name)
  initialize_meter(otel_service_name)

  logger = garf_utils.init_logging(
    loglevel='INFO', logger_type='local', name=otel_service_name
  )
  logger.addHandler(initialize_logger(otel_service_name))
  RedisInstrumentor().instrument()
  CeleryInstrumentor().instrument()


app = celery.Celery(
  'garf',
  broker=redis_url,
  backend=redis_url,
)


@app.task(pydantic=True)
def execute(request: ApiExecutorRequest):
  """Executes a single query."""
  query_executor = setup.setup_executor(
    request.source, request.context.fetcher_parameters
  )
  result = query_executor.execute(request.query, request.title, request.context)
  if isinstance(result, garf.core.GarfReport):
    return result.to_list('dict')
  return [result]


@app.task(pydantic=True)
def execute_batch(request: ApiExecutorBatchRequest):
  """Executes a batch of queries."""
  query_executor = setup.setup_executor(
    request.source, request.context.fetcher_parameters
  )
  results = query_executor.execute_batch(request.batch, request.context)
  if all(isinstance(report, garf.core.GarfReport) for report in results):
    return [report.to_list('dict') for report in results]
  return results


@app.task(pydantic=True)
def execute_workflow(
  execution_workflow: workflow.Workflow,
  selected_aliases: list[str],
  skipped_aliases: list[str],
):
  """Executes a batch of queries."""
  return workflow_runner.WorkflowRunner(
    execution_workflow=execution_workflow
  ).run(selected_aliases=selected_aliases, skipped_aliases=skipped_aliases)


@app.task(pydantic=True)
def execute_batch_in_tasks(request: ApiExecutorBatchRequest):
  """Executes each query in the batch as a separate task."""
  requests = [
    ApiExecutorRequest(
      source=request.source, title=title, query=query, context=request.context
    )
    for title, query in request.batch.items()
  ]

  job = celery.group(execute.s(r.model_dump()) for r in requests)
  return job.apply_async()
