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
"""Bootstraps executor based on provided parameters."""

from __future__ import annotations

import importlib
import logging
from typing import Any

from garf.executors import executor, fetchers
from garf.executors.api_executor import ApiQueryExecutor
from garf.executors.telemetry import tracer
from garf.io import writer

logger = logging.getLogger('garf.executors.setup')


@tracer.start_as_current_span('setup_executor')
def setup_executor(
  source: str,
  fetcher_parameters: dict[str, str | int | bool],
  enable_cache: bool = False,
  cache_ttl_seconds: int = 3600,
  simulate: bool = False,
  writers: str | list[str] | None = None,
  writer_parameters: dict[str, Any] | None = None,
) -> type[executor.Executor]:
  """Initializes executors based on a source and parameters."""
  if simulate and enable_cache:
    logger.warning('Simulating API responses. Disabling cache.')
    enable_cache = False
  if writers:
    writer_clients = writer.setup_writers(writers, writer_parameters)
  else:
    writer_clients = None
  if source == 'bq':
    bq_executor = importlib.import_module('garf.executors.bq_executor')
    query_executor = bq_executor.BigQueryExecutor(
      **fetcher_parameters, writers=writer_clients
    )
  elif source == 'sqldb':
    sql_executor = importlib.import_module('garf.executors.sql_executor')
    query_executor = (
      sql_executor.SqlAlchemyQueryExecutor.from_connection_string(
        connection_string=fetcher_parameters.get('connection_string'),
        writers=writer_clients,
      )
    )
  elif source == 'duckdb':
    duckdb_executor = importlib.import_module('garf.executors.duckdb_executor')
    query_executor = duckdb_executor.DuckDBExecutor(writers=writer_clients)
  elif source == 'opensearch':
    opensearch_executor = importlib.import_module(
      'garf.executors.opensearch_executor'
    )
    query_executor = opensearch_executor.OpenSearchQueryExecutor(
      writers=writer_clients
    )
  else:
    concrete_api_fetcher = fetchers.get_report_fetcher(source)
    if simulate:
      concrete_simulator = fetchers.get_report_simulator(source)()
    else:
      concrete_simulator = None
    query_executor = ApiQueryExecutor(
      fetcher=concrete_api_fetcher(
        **fetcher_parameters,
        enable_cache=enable_cache,
        cache_ttl_seconds=cache_ttl_seconds,
      ),
      report_simulator=concrete_simulator,
      writers=writer_clients,
    )
  return query_executor
