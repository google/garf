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
import pathlib

from garf.core import cache, report
from garf.executors import exceptions, execution_context, executor
from garf.executors.telemetry import tracer
from garf.io.writers import abs_writer

logger = logging.getLogger(__name__)


class DuckDBExecutorError(exceptions.GarfExecutorError):
  """Error when DuckDBExecutor fails to run query."""


class DuckDBExecutor(executor.Executor):
  """Handles query execution in DuckDB."""

  def __init__(
    self,
    db: str | pathlib.Path = ':memory:',
    writers: list[abs_writer.AbsWriter] | None = None,
    enable_cache: bool = False,
    cache_ttl_seconds: int = cache.DEFAULT_CACHE_TTL,
    **kwargs: str,
  ) -> None:
    """Initializes DuckDBExecutor.

    Args:
      writers: Instantiated writers.
    """
    self.writers = writers
    super().__init__(
      source='duckdb',
      enable_cache=enable_cache,
      cache_ttl_seconds=cache_ttl_seconds,
    )
    self.api_client = duckdb.connect(database=db)

  @tracer.start_as_current_span('duckdb.execute')
  def _execute(
    self,
    query: str,
    title: str,
    context: execution_context.ExecutionContext,
  ) -> report.GarfReport:
    """Executes query in DuckDB.

    Args:
      query: Location of the query.
      title: Name of the query.
      context: Query execution context.

    Returns:
      Report with data if query returns some data otherwise empty Report.
    """
    execution_result = duckdb.sql(
      query=query, connection=self.api_client
    ).to_df()
    return report.GarfReport.from_pandas(execution_result)
