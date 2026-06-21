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

# pylint: disable=C0330, g-bad-import-order, g-multiple-import, missing-class-docstring, missing-module-docstring, missing-function-docstring

import pathlib

import fastapi
from fastapi import testclient
from garf.executors.entrypoints.server import app

client = testclient.TestClient(app)

_SCRIPT_PATH = pathlib.Path(__file__).parent


class TestApiQueryExecutor:
  query = (
    'SELECT dimension.string AS resource, dimensions.string AS name, metrics.int AS clicks '
    'FROM fake'
  )

  def test_fake_source_from_query_text(self, tmp_path):
    request = {
      'source': 'fake',
      'query': self.query,
      'title': 'test',
      'context': {
        'fetcher_parameters': {
          'n_rows': 1,
        },
        'writer': 'csv',
        'writer_parameters': {'destination_folder': str(tmp_path)},
      },
    }
    response = client.post('/api/execute', json=request)
    assert response.status_code == fastapi.status.HTTP_200_OK
    tmp_path_output = f'{tmp_path}/test.csv'
    query_output_path = f'[CSV] - at {tmp_path_output}'
    expected_output = {
      'results': [query_output_path],
      'full_results': {'test': [query_output_path]},
    }
    assert response.json() == expected_output

  def test_fake_source_from_query_path(self, tmp_path):
    query_path = tmp_path / 'query.sql'
    with pathlib.Path.open(query_path, 'w', encoding='utf-8') as f:
      f.write(self.query)
    request = {
      'source': 'fake',
      'query_path': str(query_path),
      'context': {
        'fetcher_parameters': {
          'n_rows': 1,
        },
        'writer': 'csv',
        'writer_parameters': {'destination_folder': str(tmp_path)},
      },
    }
    response = client.post('/api/execute', json=request)
    assert response.status_code == fastapi.status.HTTP_200_OK
    tmp_path_output = f'{tmp_path}/query.csv'
    query_output_path = f'[CSV] - at {tmp_path_output}'
    expected_output = {
      'results': [query_output_path],
      'full_results': {str(query_path): [query_output_path]},
    }
    assert response.json() == expected_output

  def test_batch_fake_source_from_query_path(self, tmp_path):
    query_path1 = tmp_path / 'query1.sql'
    with pathlib.Path.open(query_path1, 'w', encoding='utf-8') as f:
      f.write(self.query)
    query_path2 = tmp_path / 'query2.sql'
    with pathlib.Path.open(query_path2, 'w', encoding='utf-8') as f:
      f.write(self.query)
    request = {
      'source': 'fake',
      'batch': {
        'query1': self.query,
        'query2': self.query,
      },
      'context': {
        'fetcher_parameters': {
          'n_rows': 1,
        },
        'writer': 'csv',
        'writer_parameters': {'destination_folder': str(tmp_path)},
      },
    }
    response = client.post('/api/execute:batch', json=request)
    assert response.status_code == fastapi.status.HTTP_200_OK
    expected_results = ['query1', 'query2']
    expected_full_results = {
      'query1': f'[CSV] - at {tmp_path}/query1.csv',
      'query2': f'[CSV] - at {tmp_path}/query2.csv',
    }
    assert response.json().get('results') == expected_results
    assert response.json().get('full_results') == expected_full_results

  def test_batch_returns_report_results_with_no_writer(self, tmp_path):
    query_path1 = tmp_path / 'query1.sql'
    with pathlib.Path.open(query_path1, 'w', encoding='utf-8') as f:
      f.write(self.query)
    request = {
      'source': 'fake',
      'batch': {
        'query1': self.query,
      },
      'context': {
        'fetcher_parameters': {
          'n_rows': 1,
        },
      },
    }
    response = client.post('/api/execute:batch', json=request)
    assert response.status_code == fastapi.status.HTTP_200_OK
    expected_results = ['query1']
    assert response.json().get('results') == expected_results
    expected_report_columns = ['resource', 'name', 'clicks']
    for query, result in response.json().get('full_results').items():
      assert list(result[0].keys()) == expected_report_columns

  def test_workflow_from_file(self):
    workflow_path = _SCRIPT_PATH / 'test_workflow.yaml'
    request = {
      'workflow_path': str(workflow_path),
    }
    response = client.post('/api/execute:workflow', params=request)
    assert response.status_code == fastapi.status.HTTP_200_OK
    expected_response = {
      '1-fake-test': {
        'query.sql': '[Console] - query',
        'test_query': '[Console] - test_query',
      },
    }
    assert response.json() == expected_response
