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
import json

import pytest
from garf.core import report
from garf.executors import bq_executor, execution_context
from garf.io import writer


def test_extract_datasets():
  macros = {
    'start_date': ':YYYYMMDD',
    'bq_dataset': 'dataset_1',
    'dataset_new': 'dataset_2',
    'legacy_dataset_old': 'dataset_3',
    'wrong_dts': 'dataset_4',
  }

  expected = [
    'dataset_1',
    'dataset_2',
    'dataset_3',
  ]
  datasets = bq_executor.extract_datasets(macros)
  assert datasets == expected


class TestBigQueryExecutor:
  @pytest.fixture
  def executor(self):
    return bq_executor.BigQueryExecutor(project='test')

  def test_init_raises_error_on_missing_project(self):
    with pytest.raises(
      bq_executor.BigQueryExecutorError, match='project is required'
    ):
      bq_executor.BigQueryExecutor(project=None)

  def test_init_deprecation_warning(self):
    with pytest.warns(
      DeprecationWarning,
      match=(
        "'project_id' parameter is deprecated. Please use 'project' instead."
      ),
    ):
      bq_executor.BigQueryExecutor(project_id='test-project')

  def test_execute_returns_data_to_caller(self, executor, mocker):
    query = 'SELECT 1 AS one;'
    expected_result = report.GarfReport(results=[[1]], column_names=['one'])
    mocker.patch(
      'garf.executors.bq_executor.BigQueryExecutor._execute',
      return_value=expected_result,
    )
    result = executor.execute(title='test', query=query)
    assert result == expected_result

  def test_execute_writers_data_via_executor_writer(self, mocker, tmp_path):
    writers = writer.setup_writers(
      writers=['json'], writer_parameters={'destination_folder': tmp_path}
    )
    executor = bq_executor.BigQueryExecutor(
      project='test',
      writers=writers,
    )
    expected_result = report.GarfReport(results=[[1]], column_names=['one'])
    mocker.patch(
      'garf.executors.bq_executor.BigQueryExecutor._execute',
      return_value=expected_result,
    )
    query = 'SELECT 1 AS one;'
    result = executor.execute(
      title='test',
      query=query,
    )
    output_path = str(tmp_path / 'test.json')
    assert result == f'[JSON] - at {output_path}'
    with open(output_path, 'r', encoding='utf-8') as f:
      data = json.load(f)
    assert data == [{'one': 1}]

  def test_execute_writers_data_via_context_writer(self, mocker, tmp_path):
    executor = bq_executor.BigQueryExecutor(
      project='test',
    )
    expected_result = report.GarfReport(results=[[1]], column_names=['one'])
    mocker.patch(
      'garf.executors.bq_executor.BigQueryExecutor._execute',
      return_value=expected_result,
    )
    query = 'SELECT 1 AS one;'
    result = executor.execute(
      title='test',
      query=query,
      context=execution_context.ExecutionContext(
        writer='json', writer_parameters={'destination_folder': str(tmp_path)}
      ),
    )
    output_path = str(tmp_path / 'test.json')
    assert result == f'[JSON] - at {output_path}'
    with open(output_path, 'r', encoding='utf-8') as f:
      data = json.load(f)
    assert data == [{'one': 1}]
