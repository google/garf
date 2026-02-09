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

"""Defines common functionality between executors."""

import asyncio
import inspect
import logging
from typing import Optional

from garf.core import query_editor, report, report_fetcher
from garf.executors import execution_context, query_processor
from garf.executors.telemetry import tracer
from garf.io.writers import abs_writer
from opentelemetry import trace

logger = logging.getLogger(__name__)


class Executor:
  """Defines common functionality between executors."""

  def __init__(
    self,
    preprocessors: Optional[dict[str, report_fetcher.Processor]] = None,
    postprocessors: Optional[dict[str, report_fetcher.Processor]] = None,
  ) -> None:
    self.preprocessors = preprocessors or {}
    self.postprocessors = postprocessors or {}

  @tracer.start_as_current_span('executor.execute')
  def execute(
    self,
    query: str,
    title: str,
    context: execution_context.ExecutionContext = (
      execution_context.ExecutionContext()
    ),
  ) -> report.GarfReport:
    """Executes query.

    Args:
      query: Location of the query.
      title: Name of the query.
      context: Query execution context.

    Returns:
      Report with data if query returns some data otherwise empty Report.
    """
    span = trace.get_current_span()
    query_spec = (
      query_editor.QuerySpecification(
        text=query, title=title, args=context.query_parameters
      )
      .remove_comments()
      .expand()
    )
    query_text = query_spec.query.text
    title = query_spec.query.title
    span.set_attribute('query.title', title)
    span.set_attribute('query.text', query_text)
    logger.info('Executing script: %s', title)
    results = self._execute(query=query_text, title=title, context=context)
    if results and (self.writers or context.writer):
      writer_clients = self.writers or context.writer_clients
      return write_many(writer_clients, results, title)
    span.set_attribute('execute.num_results', len(results))
    return results

  def _execute(
    self,
    query: str,
    title: str,
    context: execution_context.ExecutionContext = (
      execution_context.ExecutionContext()
    ),
  ) -> report.GarfReport:
    """Executes query."""
    raise NotImplementedError

  @tracer.start_as_current_span('executor.execute_batch')
  def execute_batch(
    self,
    batch: dict[str, str],
    context: execution_context.ExecutionContext,
    parallel_threshold: int = 10,
  ) -> list[str]:
    """Executes batch of queries for a common context.

    If an executor has any pre/post processors, executes them first while
    modifying the context.

    Args:
      batch: Mapping between query_title and its text.
      context: Execution context.
      parallel_threshold: Number of queries to execute in parallel.

    Returns:
      Results of execution.
    """
    span = trace.get_current_span()
    span.set_attribute('api.parallel_threshold', parallel_threshold)
    _handle_processors(processors=self.preprocessors, context=context)
    results = asyncio.run(
      self._run(
        batch=batch, context=context, parallel_threshold=parallel_threshold
      )
    )
    _handle_processors(processors=self.postprocessors, context=context)
    return results

  def add_preprocessor(
    self, preprocessors: dict[str, report_fetcher.Processor]
  ) -> None:
    self.preprocessors.update(preprocessors)

  async def aexecute(
    self,
    query: str,
    title: str,
    context: execution_context.ExecutionContext,
  ) -> str:
    """Performs query execution asynchronously.

    Args:
      query: Location of the query.
      title: Name of the query.
      context: Query execution context.

    Returns:
      Result of writing the report.
    """
    return await asyncio.to_thread(self.execute, query, title, context)

  async def _run(
    self,
    batch: dict[str, str],
    context: execution_context.ExecutionContext,
    parallel_threshold: int,
  ):
    semaphore = asyncio.Semaphore(value=parallel_threshold)

    async def run_with_semaphore(fn):
      async with semaphore:
        return await fn

    tasks = [
      self.aexecute(query=query, title=title, context=context)
      for title, query in batch.items()
    ]
    return await asyncio.gather(*(run_with_semaphore(task) for task in tasks))


def _handle_processors(
  processors: dict[str, report_fetcher.Processor],
  context: execution_context.ExecutionContext,
) -> None:
  context = query_processor.process_gquery(context)
  for k, processor in processors.items():
    processor_signature = list(inspect.signature(processor).parameters.keys())
    if k in context.fetcher_parameters:
      processor_parameters = {
        k: v
        for k, v in context.fetcher_parameters.items()
        if k in processor_signature
      }
      context.fetcher_parameters[k] = processor(**processor_parameters)


@tracer.start_as_current_span('executor.write')
def write_many(
  writer_clients: list[abs_writer.AbsWriter],
  results: report.GarfReport,
  title: str,
) -> Optional[str]:
  writing_results = []
  for writer_client in writer_clients:
    logger.debug(
      'Start writing data for query %s via %s writer',
      title,
      type(writer_client),
    )
    writing_result = writer_client.write(results, title)
    logger.debug(
      'Finish writing data for query %s via %s writer',
      title,
      type(writer_client),
    )
    writing_results.append(writing_result)
  logger.info('%s executed successfully', title)
  return writing_results[-1] if writing_results else None
