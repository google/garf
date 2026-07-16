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

from __future__ import annotations

import asyncio
import functools
import inspect
import logging
import operator
import time
from typing import Optional

from garf.core import query_editor, report, report_fetcher, simulator
from garf.executors import (
  exceptions,
  execution_context,
  query_processor,
  telemetry,
)
from garf.executors.telemetry import tracer
from garf.io.writers import abs_writer
from opentelemetry import trace

logger = logging.getLogger(__name__)


class Executor:
  """Defines common functionality between executors."""

  def __init__(
    self,
    source: str,
    preprocessors: Optional[dict[str, report_fetcher.Processor]] = None,
    postprocessors: Optional[dict[str, report_fetcher.Processor]] = None,
    report_simulator: Optional[simulator.ApiReportSimulator] = None,
  ) -> None:
    self.source = source
    self.preprocessors = preprocessors or {}
    self.postprocessors = postprocessors or {}
    self.simulator = report_simulator

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
    start_time = time.perf_counter()
    span = trace.get_current_span()
    executor_attributes = {'executor.class': self.__class__.__name__}
    query_spec = (
      query_editor.QuerySpecification(
        text=query, title=title, args=context.query_parameters
      )
      .remove_comments(keep_directives=True)
      .expand()
    )
    query_text = query_spec.query.text
    title = query_spec.query.title
    span.set_attribute('executor.query.title', title)
    span.set_attribute('executor.query.text', query_text)
    logger.info('Executing script: %s', title)
    if context.has_gquery:
      context = query_processor.process_gquery(context)
    if self.preprocessors and not self.simulator:
      _handle_processors(processors=self.preprocessors, context=context)
    if len(query_parts := query_spec.query_parts) > 1:
      span.set_attribute('executor.multi_query', True)
      span.set_attribute('executor.multi_query.num_queries', len(query_parts))
      no_writer_context = context.model_copy(update={'writer': 'unset'})
      batch = {f'{title}_{i}': query for i, query in enumerate(query_parts)}
      results = self.execute_batch(batch=batch, context=no_writer_context)
      results = functools.reduce(operator.add, list(results.values()))
    else:
      try:
        results = self._execute(query=query_text, title=title, context=context)
      except exceptions.GarfExecutorError as e:
        telemetry.executor_error_counter.add(1, executor_attributes)
        raise e
    if hasattr(self, 'fetcher'):
      fetcher_attributes = {
        'api.client.class': self.fetcher.api_client.__class__.__name__
      }
      executor_attributes.update(fetcher_attributes)
    telemetry.executor_counter.add(1, executor_attributes)
    if (
      (results or results.results_placeholder)
      and context.writer != 'unset'
      and (self.writers or context.writer)
    ):
      writer_clients = self.writers or context.writer_clients
      write_outputs = write_many(writer_clients, results, title)
      duration = time.perf_counter() - start_time
      telemetry.executor_histogram.record(duration, executor_attributes)
      return write_outputs
    if self.postprocessors and not self.simulator:
      _handle_processors(processors=self.postprocessors, context=context)
    duration = time.perf_counter() - start_time
    telemetry.executor_histogram.record(duration, executor_attributes)
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
  ) -> dict[str, str | report.GarfReport]:
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
    span.set_attribute('executor.parallel_threshold', parallel_threshold)
    span.set_attribute('executor.batch_size', len(batch))
    if self.preprocessors and not self.simulator:
      _handle_processors(processors=self.preprocessors, context=context)
    if context.has_gquery:
      context = query_processor.process_gquery(context)
    if len(batch) > 1:
      results = asyncio.run(
        self._run(
          batch=batch, context=context, parallel_threshold=parallel_threshold
        )
      )
      results = functools.reduce(lambda x, y: x | y, results)
    else:
      title, text = next(iter(batch.items()))
      results = {title: self.execute(query=text, title=title, context=context)}
    if self.postprocessors and not self.simulator:
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

    async def run_with_semaphore(title, fn):
      async with semaphore:
        return {title: await fn}

    tasks = {
      title: self.aexecute(query=query, title=title, context=context)
      for title, query in batch.items()
    }
    return await asyncio.gather(
      *(run_with_semaphore(title, task) for title, task in tasks.items())
    )


@tracer.start_as_current_span('executor.handle_processors')
def _handle_processors(
  processors: dict[str, report_fetcher.Processor],
  context: execution_context.ExecutionContext,
) -> list[str]:
  processed = []
  if context.has_gquery:
    context = query_processor.process_gquery(context)
  for k, processor in processors.items():
    processor_signature = list(inspect.signature(processor).parameters.keys())
    if k == 'init' or k in context.fetcher_parameters:
      processor_parameters = {
        k: v
        for k, v in {
          **context.fetcher_parameters,
          **context.query_parameters.model_dump(),
        }.items()
        if k in processor_signature
      }
      context.fetcher_parameters[k] = processor(**processor_parameters)
      processed.append(k)
  for p in processed:
    processors.pop(p, None)


@tracer.start_as_current_span('executor.write')
def write_many(
  writer_clients: list[abs_writer.AbsWriter],
  results: report.GarfReport,
  title: str,
) -> Optional[str]:
  span = trace.get_current_span()
  span.set_attributes(
    {
      'executor.writers': [
        writer.__class__.__name__ for writer in writer_clients
      ],
      'executor.report.num_rows': len(results),
      'executor.report.num_column': len(results.column_names),
    }
  )
  if not results:
    span.set_attribute('executor.report.is_placeholder', True)

  writing_results = []
  for writer_client in writer_clients:
    start_time = time.perf_counter()
    logger.debug(
      'Start writing data for query %s via %s writer',
      title,
      type(writer_client),
    )
    writing_result = writer_client.write(results, title)
    duration = time.perf_counter() - start_time
    telemetry.write_histogram.record(
      duration, {'writer_class': writer_client.__class__.__name__}
    )
    logger.debug(
      'Finish writing data for query %s via %s writer',
      title,
      type(writer_client),
    )
    writing_results.append(writing_result)
  logger.info('%s executed successfully', title)
  return writing_results[-1] if writing_results else None
