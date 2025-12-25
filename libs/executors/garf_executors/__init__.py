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
"""Executors to fetch data from various APIs."""

from __future__ import annotations

import importlib

from garf_executors import executor, fetchers
from garf_executors.api_executor import ApiExecutionContext, ApiQueryExecutor
from garf_executors.telemetry import tracer


@tracer.start_as_current_span('setup_executor')
def setup_executor(
  source: str,
  fetcher_parameters: dict[str, str | int | bool],
  enable_cache: bool = False,
  cache_ttl_seconds: int = 3600,
) -> type[executor.Executor]:
  """Initializes executors based on a source and parameters."""
  if source == 'bq':
    bq_executor = importlib.import_module('garf_executors.bq_executor')
    query_executor = bq_executor.BigQueryExecutor(**fetcher_parameters)
  elif source == 'sqldb':
    sql_executor = importlib.import_module('garf_executors.sql_executor')
    query_executor = (
      sql_executor.SqlAlchemyQueryExecutor.from_connection_string(
        fetcher_parameters.get('connection_string')
      )
    )
  else:
    concrete_api_fetcher = fetchers.get_report_fetcher(source)
    query_executor = ApiQueryExecutor(
      concrete_api_fetcher(
        **fetcher_parameters,
        enable_cache=enable_cache,
        cache_ttl_seconds=cache_ttl_seconds,
      )
    )
  return query_executor


__all__ = [
  'ApiQueryExecutor',
  'ApiExecutionContext',
]

__version__ = '0.1.7'
