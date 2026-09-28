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


import pathlib

from garf.core import report
from garf.executors import duckdb_executor, execution_context
from garf.io import reader

_SCRIPT_PATH = pathlib.Path(__file__).parent


class TestDuckDBExecutor:
  def test_execute(self):
    test_executor = duckdb_executor.DuckDBExecutor()

    query = reader.FileReader().read(_SCRIPT_PATH / 'data/duckdb.sql')

    result = test_executor.execute(
      query=query,
      title='test',
      context=execution_context.ExecutionContext(
        query_parameters={
          'macro': {
            'file': str(_SCRIPT_PATH / 'data/example.json'),
            'another_file': str(_SCRIPT_PATH / 'data/example.csv'),
          }
        }
      ),
    )
    expected_report = report.GarfReport(
      results=[
        [1, 2, 20],
        [2, 3, 30],
        [4, 5, 50],
      ],
      column_names=['key', 'value', 'new_value'],
    )

    assert result == expected_report

  def test_execute_works_with_default_in_memory_db(self):
    executor1 = duckdb_executor.DuckDBExecutor()
    executor2 = duckdb_executor.DuckDBExecutor()
    executor1.execute(
      title='test',
      query='CREATE TABLE test_executor_1 AS SELECT 1 AS one;',
    )

    result = executor2.execute(
      title='test_executor_2',
      query='SELECT * FROM test_executor_1;',
    )
    expected_result = report.GarfReport(results=[[1]], column_names=['one'])
    assert result == expected_result
