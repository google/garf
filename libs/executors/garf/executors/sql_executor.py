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
from garf.core import query_editor, report
from garf.executors import exceptions, execution_context, executor
from garf.executors.telemetry import tracer
from garf.io.writers import abs_writer
from opentelemetry import trace

logger = logging.getLogger(__name__)


class SqlAlchemyQueryExecutorError(exceptions.GarfExecutorError):
  """Error when SqlAlchemyQueryExecutor fails to run query."""


class SqlAlchemyQueryExecutor(executor.Executor):
  """Handles query execution via SqlAlchemy.

  Attributes:
      engine: Initialized Engine object to operated on a given database.
  """

  def __init__(
    self,
    engine: sqlalchemy.engine.base.Engine | None = None,
    writers: list[abs_writer.AbsWriter] | None = None,
    **kwargs: str,
  ) -> None:
    """Initializes executor with a given engine.

    Args:
        engine: Initialized Engine object to operated on a given database.
    """
    self.engine = engine or sqlalchemy.create_engine('sqlite://')
    self.writers = writers
    super().__init__()

  @classmethod
  def from_connection_string(
    cls, connection_string: str | None, writers: list[str] | None = None
  ) -> SqlAlchemyQueryExecutor:
    """Creates executor from SqlAlchemy connection string.

    https://docs.sqlalchemy.org/en/20/core/engines.html
    """
    engine = sqlalchemy.create_engine(connection_string or 'sqlite://')
    return cls(engine=engine, writers=writers)

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
    with self.engine.begin() as conn:
      if re.findall(r'(create|update) ', query_text.lower()):
        try:
          conn.connection.executescript(query_text)
          results = report.GarfReport()
        except Exception as e:
          raise SqlAlchemyQueryExecutorError(
            f'Failed to execute query {title}: Reason: {e}'
          ) from e
      else:
        temp_table_name = f'temp_{uuid.uuid4().hex}'
        query_text = f'CREATE TABLE {temp_table_name} AS {query_text}'
        conn.connection.executescript(query_text)
        try:
          results = report.GarfReport.from_pandas(
            pd.read_sql(f'SELECT * FROM {temp_table_name}', conn)
          )
        except Exception as e:
          raise SqlAlchemyQueryExecutorError(
            f'Failed to execute query {title}: Reason: {e}'
          ) from e
        finally:
          conn.connection.execute(f'DROP TABLE {temp_table_name}')
      if results and (self.writers or context.writer):
        writer_clients = self.writers or context.writer_clients
        return executor.write_many(writer_clients, results, title)
      span.set_attribute('execute.num_results', len(results))
      return results
