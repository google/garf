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

"""Executes SQL queries over local files via DuckDB."""

from __future__ import annotations

try:
  import duckdb
except ImportError as e:
  raise ImportError(
    'Please install garf-executors with DuckDB support '
    '- `pip install garf-executors[duckdb]`'
  ) from e

import logging

from garf.core import query_editor, report
from garf.executors import exceptions, execution_context, executor
from garf.executors.telemetry import tracer
from garf.io.writers import abs_writer
from opentelemetry import trace

logger = logging.getLogger(__name__)


class DuckDBExecutorError(exceptions.GarfExecutorError):
  """Error when DuckDBExecutor fails to run query."""


class DuckDBExecutor(executor.Executor):
  """Handles query execution in DuckDB."""

  def __init__(
    self,
    writers: list[abs_writer.AbsWriter] | None = None,
    **kwargs: str,
  ) -> None:
    """Initializes DuckDBExecutor.

    Args:
      writers: Instantiated writers.
    """
    self.writers = writers
    super().__init__(**kwargs)

  @tracer.start_as_current_span('duckdb.execute')
  def execute(
    self,
    query: str,
    title: str,
    context: execution_context.ExecutionContext = (
      execution_context.ExecutionContext()
    ),
  ) -> report.GarfReport:
    """Executes query in DuckDB.

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
    span.set_attribute('query.text', query)
    logger.info('Executing script: %s', title)
    with tracer.start_as_current_span('duckdb.sql'):
      execution_result = duckdb.sql(query_text).to_df()
    results = report.GarfReport.from_pandas(execution_result)
    if results and (self.writers or context.writer):
      writer_clients = self.writers or context.writer_clients
      if not writer_clients:
        logger.warning('No writers configured, skipping write operation')
      else:
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
        # Return the last writer's result for backward compatibility
        logger.info('%s executed successfully', title)
        return writing_results[-1] if writing_results else None
    logger.info('%s executed successfully', title)
    span.set_attribute('execute.num_results', len(results))
    return results
