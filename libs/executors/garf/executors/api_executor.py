# Copyright 2024 Google LLC
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
"""Module for executing Garf queries and writing them to local/remote.

ApiQueryExecutor performs fetching data from API in a form of
GarfReport and saving it to local/remote storage.
"""
# pylint: disable=C0330, g-bad-import-order, g-multiple-import

from __future__ import annotations

import logging
import pathlib

from garf.core import report_fetcher, simulator
from garf.executors import (
  exceptions,
  execution_context,
  executor,
  fetchers,
  query_processor,
)
from garf.executors.telemetry import tracer
from opentelemetry import metrics, trace

logger = logging.getLogger(__name__)
meter = metrics.get_meter('garf.executors')

api_counter = meter.create_counter(
  'garf_api_execute_total',
  unit='1',
  description='Counts number of API executions',
)


class ApiExecutionContext(execution_context.ExecutionContext):
  """Common context for executing one or more queries."""

  writer: str | list[str] = 'console'


class ApiQueryExecutor(executor.Executor):
  """Gets data from API and writes them to local/remote storage.

  Attributes:
      api_client: a client used for connecting to API.
  """

  def __init__(
    self,
    fetcher: report_fetcher.ApiReportFetcher,
    report_simulator: simulator.ApiReportSimulator | None = None,
  ) -> None:
    """Initializes ApiQueryExecutor.

    Args:
      fetcher: Instantiated report fetcher.
      report_simulator: Instantiated simulator.
    """
    self.fetcher = fetcher
    self.simulator = report_simulator
    super().__init__(
      preprocessors=self.fetcher.preprocessors,
      postprocessors=self.fetcher.postprocessors,
    )

  @classmethod
  def from_fetcher_alias(
    cls,
    source: str,
    fetcher_parameters: dict[str, str] | None = None,
    enable_cache: bool = False,
    cache_ttl_seconds: int = 3600,
  ) -> ApiQueryExecutor:
    if not fetcher_parameters:
      fetcher_parameters = {}
    concrete_api_fetcher = fetchers.get_report_fetcher(source)
    return ApiQueryExecutor(
      fetcher=concrete_api_fetcher(
        **fetcher_parameters,
        enable_cache=enable_cache,
        cache_ttl_seconds=cache_ttl_seconds,
      )
    )

  @tracer.start_as_current_span('api.execute')
  def execute(
    self,
    query: str,
    title: str,
    context: ApiExecutionContext,
  ) -> str:
    """Reads query, extract results and stores them in a specified location.

    Args:
      query: Location of the query.
      title: Name of the query.
      context: Query execution context.

    Returns:
      Result of writing the report.

    Raises:
      GarfExecutorError: When failed to execute query.
    """
    if self.simulator:
      return self.simulate(query=query, title=title, context=context)
    context = query_processor.process_gquery(context)
    span = trace.get_current_span()
    span.set_attribute('fetcher.class', self.fetcher.__class__.__name__)
    span.set_attribute(
      'api.client.class', self.fetcher.api_client.__class__.__name__
    )
    try:
      span.set_attribute('query.title', title)
      span.set_attribute('query.text', query)
      logger.debug('starting query %s', query)
      title = pathlib.Path(title).name.split('.')[0]
      api_counter.add(
        1, {'api.client.class': self.fetcher.api_client.__class__.__name__}
      )
      results = self.fetcher.fetch(
        query_specification=query,
        args=context.query_parameters,
        title=title,
        **context.fetcher_parameters,
      )
      writer_clients = context.writer_clients
      if not writer_clients:
        logger.warning('No writers configured, skipping write operation')
        return None
      writing_results = []
      for writer_client in writer_clients:
        logger.debug(
          'Start writing data for query %s via %s writer',
          title,
          type(writer_client),
        )
        result = writer_client.write(results, title)
        logger.debug(
          'Finish writing data for query %s via %s writer',
          title,
          type(writer_client),
        )
        writing_results.append(result)
      logger.info('%s executed successfully', title)
      # Return the last writer's result for backward compatibility
      return writing_results[-1] if writing_results else None
    except Exception as e:
      logger.error('%s generated an exception: %s', title, str(e))
      raise exceptions.GarfExecutorError(
        '%s generated an exception: %s', title, str(e)
      ) from e

  @tracer.start_as_current_span('api.simulate')
  def simulate(
    self,
    query: str,
    title: str,
    context: ApiExecutionContext,
  ) -> str:
    """Reads query, simulates results and stores them in a specified location.

    Args:
      query: Location of the query.
      title: Name of the query.
      context: Query execution context.

    Returns:
      Result of writing the report.

    Raises:
      GarfExecutorError: When failed to execute query.
    """
    context = query_processor.process_gquery(context)
    span = trace.get_current_span()
    span.set_attribute('fetcher.class', self.fetcher.__class__.__name__)
    span.set_attribute(
      'api.client.class', self.fetcher.api_client.__class__.__name__
    )
    try:
      span.set_attribute('query.title', title)
      span.set_attribute('query.text', query)
      logger.debug('starting query %s', query)
      title = pathlib.Path(title).name.split('.')[0]
      results = self.simulator.simulate(
        query_specification=query,
        title=title,
        **context.fetcher_parameters,
      )
      writer_clients = context.writer_clients
      if not writer_clients:
        logger.warning('No writers configured, skipping write operation')
        return None
      writing_results = []
      for writer_client in writer_clients:
        logger.debug(
          'Start writing data for query %s via %s writer',
          title,
          type(writer_client),
        )
        result = writer_client.write(results, title)
        logger.debug(
          'Finish writing data for query %s via %s writer',
          title,
          type(writer_client),
        )
        writing_results.append(result)
      logger.info('%s executed successfully', title)
      # Return the last writer's result for backward compatibility
      return writing_results[-1] if writing_results else None
    except Exception as e:
      logger.error('%s generated an exception: %s', title, str(e))
      raise exceptions.GarfExecutorError(
        '%s generated an exception: %s', title, str(e)
      ) from e
