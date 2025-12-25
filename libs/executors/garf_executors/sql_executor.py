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
"""Defines mechanism for executing queries via SqlAlchemy."""

from __future__ import annotations

try:
  import sqlalchemy
except ImportError as e:
  raise ImportError(
    'Please install garf-executors with sqlalchemy support '
    '- `pip install garf-executors[sqlalchemy]`'
  ) from e

import logging
import re
import uuid

import pandas as pd
from garf_core import query_editor, report
from opentelemetry import trace

from garf_executors import exceptions, execution_context, executor
from garf_executors.telemetry import tracer

logger = logging.getLogger(__name__)


class SqlAlchemyQueryExecutorError(exceptions.GarfExecutorError):
  """Error when SqlAlchemyQueryExecutor fails to run query."""


class SqlAlchemyQueryExecutor(
  executor.Executor, query_editor.TemplateProcessorMixin
):
  """Handles query execution via SqlAlchemy.

  Attributes:
      engine: Initialized Engine object to operated on a given database.
  """

  def __init__(self, engine: sqlalchemy.engine.base.Engine) -> None:
    """Initializes executor with a given engine.

    Args:
        engine: Initialized Engine object to operated on a given database.
    """
    self.engine = engine

  @classmethod
  def from_connection_string(
    cls, connection_string: str
  ) -> SqlAlchemyQueryExecutor:
    """Creates executor from SqlAlchemy connection string.

    https://docs.sqlalchemy.org/en/20/core/engines.html
    """
    engine = sqlalchemy.create_engine(connection_string)
    return cls(engine)

  @tracer.start_as_current_span('sql.execute')
  def execute(
    self,
    query: str,
    title: str,
    context: execution_context.ExecutionContext = (
      execution_context.ExecutionContext()
    ),
  ) -> report.GarfReport:
    """Executes query in a given database via SqlAlchemy.

    Args:
      query: Location of the query.
      title: Name of the query.
      context: Query execution context.

    Returns:
      Report with data if query returns some data otherwise empty Report.
    """
    span = trace.get_current_span()
    logging.info('Executing script: %s', title)
    query_text = self.replace_params_template(query, context.query_parameters)
    with self.engine.begin() as conn:
      if re.findall(r'(create|update) ', query_text.lower()):
        conn.connection.executescript(query_text)
        results = report.GarfReport()
      else:
        temp_table_name = f'temp_{uuid.uuid4().hex}'
        query_text = f'CREATE TABLE {temp_table_name} AS {query_text}'
        conn.connection.executescript(query_text)
        try:
          results = report.GarfReport.from_pandas(
            pd.read_sql(f'SELECT * FROM {temp_table_name}', conn)
          )
        finally:
          conn.connection.execute(f'DROP TABLE {temp_table_name}')
      if context.writer and results:
        writer_clients = context.writer_clients
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
          logger.info('%s executed successfully', title)
          # Return the last writer's result for backward compatibility
          return writing_results[-1] if writing_results else None
      span.set_attribute('execute.num_results', len(results))
      return results
