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

import contextlib
import importlib
import json
import logging
from typing import Any

import garf.core
from garf.executors import executor, fetchers
from garf.executors.api_executor import ApiQueryExecutor
from garf.executors.telemetry import tracer
from garf.io import writer
from opentelemetry import trace

logger = logging.getLogger('garf.executors.setup')

_EXECUTORS_MODULES: dict[str, str] = {
  'bq': {
    'import_path': 'garf.executors.bq_executor',
    'executor_class': 'BigQueryExecutor',
  },
  'sqldb': {
    'import_path': 'garf.executors.sql_executor',
    'executor_class': 'SqlAlchemyQueryExecutor',
  },
  'duckdb': {
    'import_path': 'garf.executors.duckdb_executor',
    'executor_class': 'DuckDBExecutor',
  },
  'opensearch': {
    'import_path': 'garf.executors.opensearch_executor',
    'executor_class': 'OpenSearchQueryExecutor',
  },
  'elasticearch': {
    'import_path': 'garf.executors.elasticsearch_executor',
    'executor_class': 'ElasticSearchQueryExecutor',
  },
}


def available_executors() -> set[str]:
  executors = []
  for k, v in _EXECUTORS_MODULES.items():
    with contextlib.suppress(ImportError):
      importlib.import_module(v.get('import_path'))
      executors.append(k)
  return executors


def find_executors() -> set[str]:
  available_fetchers = fetchers.find_fetchers()
  available_executors = {'bq', 'duckdb', 'opensearch', 'sqldb', 'elasticsearch'}
  return sorted(available_fetchers | available_executors)


@tracer.start_as_current_span('executor.setup')
def setup_executor(
  source: str,
  fetcher_parameters: dict[str, str | int | bool],
  enable_cache: bool = False,
  cache_ttl_seconds: int = garf.core.cache.DEFAULT_CACHE_TTL,
  simulate: bool = False,
  writers: str | list[str] | None = None,
  writer_parameters: dict[str, Any] | None = None,
) -> type[executor.Executor]:
  """Initializes executors based on a source and parameters."""
  span = trace.get_current_span()
  span.set_attribute('executor.source', source)
  if fetcher_parameters:
    span.set_attribute(
      'executor.source.parameters',
      json.dumps({k: v for k, v in fetcher_parameters.items() if v}),
    )
  if simulate and enable_cache:
    logger.warning('Simulating API responses. Disabling cache.')
    enable_cache = False
  if writers:
    span.set_attribute('executor.writers', writers)
    if writer_parameters:
      span.set_attribute(
        'executor.writer.parameters',
        json.dumps({k: v for k, v in writer_parameters.items() if v}),
      )
    writer_clients = writer.setup_writers(writers, writer_parameters)
  else:
    writer_clients = None
  if concrete_executor_module := _EXECUTORS_MODULES.get(source):
    executor_module = importlib.import_module(
      concrete_executor_module.get('import_path')
    )
    query_executor = getattr(
      executor_module, concrete_executor_module.get('executor_class')
    )(**fetcher_parameters, writers=writer_clients)
  else:
    concrete_api_fetcher = fetchers.get_report_fetcher(source)
    if simulate:
      span.set_attribute('executor.simulate', True)
      concrete_simulator = fetchers.get_report_simulator(source)()
    else:
      concrete_simulator = None
    query_executor = ApiQueryExecutor(
      fetcher=concrete_api_fetcher(
        **fetcher_parameters,
        enable_cache=enable_cache,
        cache_ttl_seconds=cache_ttl_seconds
        or garf.core.cache.DEFAULT_CACHE_TTL,
      ),
      report_simulator=concrete_simulator,
      writers=writer_clients,
      source=source,
    )
  if enable_cache:
    span.set_attributes(
      {
        'executor.cache': True,
        'executor.cache.location': query_executor.fetcher.cache.location,
        'executor.cache.ttl_seconds': (
          query_executor.fetcher.cache.ttl_seconds
        ),
        'executor.cache.provider': (
          query_executor.fetcher.cache.cache_provider.__class__.__name__
        ),
      }
    )
  return query_executor
