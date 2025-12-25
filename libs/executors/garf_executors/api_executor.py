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

from garf_core import report_fetcher
from opentelemetry import trace

from garf_executors import exceptions, execution_context, executor, fetchers
from garf_executors.telemetry import tracer

logger = logging.getLogger(__name__)


class ApiExecutionContext(execution_context.ExecutionContext):
  """Common context for executing one or more queries."""

  writer: str | list[str] = 'console'


class ApiQueryExecutor(executor.Executor):
  """Gets data from API and writes them to local/remote storage.

  Attributes:
      api_client: a client used for connecting to API.
  """

  def __init__(self, fetcher: report_fetcher.ApiReportFetcher) -> None:
    """Initializes ApiQueryExecutor.

    Args:
        fetcher: Instantiated report fetcher.
    """
    self.fetcher = fetcher

  @classmethod
  def from_fetcher_alias(
    cls, source: str, fetcher_parameters: dict[str, str] | None = None
  ) -> ApiQueryExecutor:
    if not fetcher_parameters:
      fetcher_parameters = {}
    concrete_api_fetcher = fetchers.get_report_fetcher(source)
    return ApiQueryExecutor(concrete_api_fetcher(**fetcher_parameters))

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
    span = trace.get_current_span()
    span.set_attribute('fetcher', self.fetcher.__class__.__name__)
    span.set_attribute('api_client', self.fetcher.api_client.__class__.__name__)
    try:
      span.set_attribute('query_title', title)
      span.set_attribute('query_text', query)
      logger.debug('starting query %s', query)
      results = self.fetcher.fetch(
        query_specification=query,
        args=context.query_parameters,
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
