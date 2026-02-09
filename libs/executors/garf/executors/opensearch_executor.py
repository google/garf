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
"""Executes SQL queries via OpenSearch."""

from __future__ import annotations

try:
  from opensearchpy import OpenSearch
except ImportError as e:
  raise ImportError(
    'Please install garf-executors with OpenSearch support - '
    '`pip install garf-executors[opensearch]`'
  ) from e


import logging

from garf.core import report
from garf.executors import exceptions, execution_context, executor
from garf.executors.telemetry import tracer
from garf.io.writers import abs_writer

logger = logging.getLogger(__name__)


class OpenSearchQueryExecutorError(exceptions.GarfExecutorError):
  """Error when OpenSearchQueryExecutor fails to run query."""


class OpenSearchQueryExecutor(executor.Executor):
  """Handles query execution via OpenSearch SQL plugin.

  Attributes:
    client: Initialized OpenSearch client.
  """

  def __init__(
    self,
    client: OpenSearch | None = None,
    writers: list[abs_writer.AbsWriter] | None = None,
    **kwargs: str,
  ) -> None:
    """Initializes executor with a given OpenSearch client.

    Args:
      client: Initialized OpenSearch client.
      writers: Initialized writers.
    """
    self.client = client or OpenSearch(
      hosts=[{'host': 'localhost', 'port': 9200}]
    )
    self.writers = writers
    super().__init__()

  @tracer.start_as_current_span('opensearch.execute')
  def _execute(
    self, query: str, title: str, context: execution_context.ExecutionContext
  ) -> report.GarfReport:
    """Executes query in a given database via SqlAlchemy.

    Args:
      query: Location of the query.
      title: Name of the query.
      context: Query execution context.

    Returns:
      Report with data if query returns some data otherwise empty Report.
    """
    response = self.client.transport.perform_request(
      'POST', '/_plugins/_sql', body={'query': query}
    )
    if 'datarows' in response and 'schema' in response:
      data = []
      headers = [col['name'] for col in response['schema']]
      for row in response['datarows']:
        data.append(row)
      return report.GarfReport(results=data, column_names=headers)
    return report.GarfReport()
