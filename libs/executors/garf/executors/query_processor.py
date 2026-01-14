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

import contextlib

from garf.core import query_editor
from garf.executors import exceptions, execution_context


def process_gquery(
  context: execution_context.ExecutionContext,
) -> execution_context.ExecutionContext:
  for k, v in context.fetcher_parameters.items():
    if isinstance(v, str) and v.startswith('gquery'):
      no_writer_context = context.model_copy(update={'writer': None})
      try:
        _, alias, query = v.split(':', maxsplit=3)
      except ValueError:
        raise exceptions.GarfExecutorError(
          f'Incorrect gquery format, should be gquery:alias:query, got {v}'
        )
      if alias == 'sqldb':
        from garf.executors import sql_executor

        gquery_executor = sql_executor.SqlAlchemyQueryExecutor(
          **context.fetcher_parameters
        )
      elif alias == 'bq':
        from garf.executors import bq_executor

        gquery_executor = bq_executor.BigQueryExecutor(
          **context.fetcher_parameters
        )
      else:
        raise exceptions.GarfExecutorError(
          f'Unsupported alias for gquery: {alias}'
        )
      with contextlib.suppress(query_editor.GarfResourceError):
        query_spec = query_editor.QuerySpecification(
          text=query, args=context.query_parameters
        ).generate()
        if len(columns := [c for c in query_spec.column_names if c != '_']) > 1:
          raise exceptions.GarfExecutorError(
            f'Multiple columns in gquery: {columns}'
          )
      res = gquery_executor.execute(
        query=query, title='gquery', context=no_writer_context
      )
      context.fetcher_parameters[k] = res.to_list(row_type='scalar')
  return context
