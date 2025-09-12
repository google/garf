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
"""Executors to fetch data from various APIS and postprocess them."""

from __future__ import annotations

from garf_executors import bq_executor, fetchers, sql_executor
from garf_executors.api_executor import ApiExecutionContext, ApiQueryExecutor


def setup_executor(source: str, fetcher_parameters: dict[str, str]):
  """Initializes executors based on a source and parameters."""
  if source == 'bq':
    return bq_executor.BigQueryExecutor(**fetcher_parameters)
  if source == 'sqldb':
    return sql_executor.SqlAlchemyQueryExecutor.from_connection_string(
      fetcher_parameters.get('connection_string')
    )
  concrete_api_fetcher = fetchers.get_report_fetcher(source)
  return ApiQueryExecutor(concrete_api_fetcher(**fetcher_parameters))


__all__ = [
  'ApiQueryExecutor',
  'ApiExecutionContext',
]

__version__ = '0.0.8'
