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

import re

import pytest
from garf.executors import exceptions, execution_context, query_processor


def test_process_gquery_returns_unchanged_context():
  context = execution_context.ExecutionContext(fetcher_parameters={'id': 1})
  processed_context = query_processor.process_gquery(context)
  assert processed_context == context


@pytest.mark.parametrize(
  ('gquery', 'error_message'),
  [
    (
      'gquery',
      'Incorrect gquery format, should be gquery:alias:query, got gquery',
    ),
    (
      'gquery::SELECT 1',
      'Missing alias in gquery: gquery::SELECT 1',
    ),
    (
      'gquery:sqldb',
      'Missing query text in gquery: gquery:sqldb',
    ),
    (
      'gquery:unknown_alias:SELECT 1',
      'Unsupported alias unknown_alias for gquery: gquery:unknown_alias:SELECT 1',
    ),
    (
      'gquery:sqldb:SELECT 1 AS id, 2 AS second_id',
      "Multiple columns in gquery definition: ['id', 'second_id']",
    ),
  ],
)
def test_process_gquery_raises_error(gquery, error_message):
  context = execution_context.ExecutionContext(
    fetcher_parameters={'id': gquery}
  )
  with pytest.raises(
    query_processor.GqueryError,
    match=re.escape(error_message),
  ):
    query_processor.process_gquery(context)


def test_process_gquery_returns_processed_context():
  context = execution_context.ExecutionContext(
    fetcher_parameters={'id': 'gquery:sqldb:SELECT 1 AS id'}
  )
  processed_context = query_processor.process_gquery(context)
  expected_context = execution_context.ExecutionContext(
    fetcher_parameters={'id': [1]}
  )
  assert processed_context == expected_context
