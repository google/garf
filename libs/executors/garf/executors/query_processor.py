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

"""qQuery can be used as a parameter in garf queries."""

import contextlib

from garf.core import query_editor, query_parser
from garf.executors import execution_context


class GqueryError(query_parser.GarfQueryError):
  """Errors on incorrect qQuery syntax."""


def _handle_sub_context(context, sub_context):
  for k, v in sub_context.items():
    if isinstance(v, str) and v.startswith('gquery'):
      no_writer_context = context.model_copy(update={'writer': None})
      try:
        _, alias, *query = v.split(':', maxsplit=3)
      except ValueError:
        raise GqueryError(
          f'Incorrect gquery format, should be gquery:alias:query, got {v}'
        )
      if not alias:
        raise GqueryError(f'Missing alias in gquery: {v}')
      if not query:
        raise GqueryError(f'Missing query text in gquery: {v}')
      if alias == 'sqldb':
        from garf.executors import sql_executor

        gquery_executor = (
          sql_executor.SqlAlchemyQueryExecutor.from_connection_string(
            context.fetcher_parameters.get('connection_string')
          )
        )
      elif alias == 'bq':
        from garf.executors import bq_executor

        gquery_executor = bq_executor.BigQueryExecutor(
          **context.fetcher_parameters
        )
      else:
        raise GqueryError(f'Unsupported alias {alias} for gquery: {v}')
      with contextlib.suppress(
        query_editor.GarfResourceError, query_parser.GarfVirtualColumnError
      ):
        query = ':'.join(query)
        query_spec = query_editor.QuerySpecification(
          text=query, args=context.query_parameters
        ).generate()
        if len(columns := [c for c in query_spec.column_names if c != '_']) > 1:
          raise GqueryError(f'Multiple columns in gquery definition: {columns}')
      res = gquery_executor.execute(
        query=query, title='gquery', context=no_writer_context
      )
      if len(columns := [c for c in res.column_names if c != '_']) > 1:
        raise GqueryError(f'Multiple columns in gquery result: {columns}')
      sub_context[k] = res.to_list(row_type='scalar')


def process_gquery(
  context: execution_context.ExecutionContext,
) -> execution_context.ExecutionContext:
  _handle_sub_context(context, context.fetcher_parameters)
  _handle_sub_context(context, context.query_parameters.macro)
  return context
