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
from garf.executors import exceptions, setup, telemetry
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

CACHE_ENABLED = os.getenv('GARF_CACHE_LOCATION')
redis_url = os.getenv('CELERY_BROKER_URL', 'redis://localhost:6379/0')


class ApiExecutorRequest(pydantic.BaseModel):
  """Request for executing a query.

  Attributes:
    source: Type of API to interact with.
    title: Name of the query used as an output for writing.
    query: Query to execute.
    query_path: Local or remote path to query.
    context: Execution context.
    enable_cache: Whether to store report in a cache.
    cache_ttl_seconds: TTL of cached report.
    simulate: Whether to simulate response from API.
  """

  source: str
  title: Optional[str] = None
  query: Optional[str] = None
  query_path: Optional[Union[str, list[str]]] = None
  context: garf.executors.execution_context.ExecutionContext
  enable_cache: bool = False
  cache_ttl_seconds: int = garf.core.cache.DEFAULT_CACHE_TTL
  simulate: bool = False

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
    enable_cache: Whether to store report in a cache.
    cache_ttl_seconds: TTL of cached report.
    simulate: Whether to simulate response from API.
  """

  source: str
  batch: dict[str, str]
  context: garf.executors.execution_context.ExecutionContext
  enable_cache: bool = False
  cache_ttl_seconds: int = garf.core.cache.DEFAULT_CACHE_TTL
  simulate: bool = False


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
    source=request.source,
    fetcher_parameters=request.context.fetcher_parameters,
    enable_cache=request.enable_cache if CACHE_ENABLED else False,
    cache_ttl_seconds=request.cache_ttl_seconds,
    simulate=request.simulate,
  )
  telemetry.executor_active_executions.add(
    1, attributes={'executor.source': query_executor.source}
  )
  result = query_executor.execute(request.query, request.title, request.context)
  telemetry.executor_active_executions.add(
    -1, attributes={'executor.source': query_executor.source}
  )
  if isinstance(result, garf.core.GarfReport):
    return result.to_list('dict')
  return [result]


@app.task(pydantic=True)
def execute_batch(request: ApiExecutorBatchRequest):
  """Executes a batch of queries."""
  n_queries = len(request.batch)
  query_executor = setup.setup_executor(
    source=request.source,
    fetcher_parameters=request.context.fetcher_parameters,
    enable_cache=request.enable_cache if CACHE_ENABLED else False,
    cache_ttl_seconds=request.cache_ttl_seconds,
    simulate=request.simulate,
  )
  telemetry.executor_active_executions.add(
    n_queries, attributes={'executor.source': query_executor.source}
  )
  results = query_executor.execute_batch(request.batch, request.context)
  telemetry.executor_active_executions.add(
    -n_queries, attributes={'executor.source': query_executor.source}
  )
  if all(
    isinstance(report, garf.core.GarfReport) for report in results.values()
  ):
    return {query: report.to_list('dict') for query, report in results.items()}
  return results


@app.task(pydantic=True)
def execute_workflow(
  execution_workflow: workflow.Workflow,
  selected_aliases: list[str],
  skipped_aliases: list[str],
  simulate: bool = False,
):
  """Executes a batch of queries."""
  runner = workflow_runner.WorkflowRunner(execution_workflow=execution_workflow)
  garf.executors.version.validate_version(
    runner.workflow.metadata.required_garf_version
  )
  telemetry.executor_active_workflows.add(1)
  results = runner.run(
    selected_aliases=selected_aliases,
    skipped_aliases=skipped_aliases,
    simulate=simulate,
  )
  telemetry.executor_active_workflows.add(-1)
  return results


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
