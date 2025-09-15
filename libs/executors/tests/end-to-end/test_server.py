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
from garf_executors.entrypoints.server import router

app = fastapi.FastAPI()
app.include_router(router)
client = testclient.TestClient(app)

_SCRIPT_PATH = pathlib.Path(__file__).parent


class TestApiQueryExecutor:
  query = (
    'SELECT resource, dimensions.name AS name, metrics.clicks AS clicks '
    'FROM resource'
  )

  def test_fake_source_from_query_text(self, tmp_path):
    fake_data = _SCRIPT_PATH / 'test.json'
    request = {
      'source': 'fake',
      'query': self.query,
      'title': 'test',
      'context': {
        'fetcher_parameters': {
          'data_location': str(fake_data),
        },
        'writer': 'csv',
        'writer_parameters': {'destination_folder': str(tmp_path)},
      },
    }
    response = client.post('/api/execute', json=request)
    assert response.status_code == fastapi.status.HTTP_200_OK
    expected_output = {'results': [f'[CSV] - at {tmp_path}/test.csv']}
    assert response.json() == expected_output

  def test_fake_source_from_query_path(self, tmp_path):
    query_path = tmp_path / 'query.sql'
    with pathlib.Path.open(query_path, 'w', encoding='utf-8') as f:
      f.write(self.query)
    fake_data = _SCRIPT_PATH / 'test.json'
    request = {
      'source': 'fake',
      'query_path': str(query_path),
      'context': {
        'fetcher_parameters': {
          'data_location': str(fake_data),
        },
        'writer': 'csv',
        'writer_parameters': {'destination_folder': str(tmp_path)},
      },
    }
    response = client.post('/api/execute', json=request)
    assert response.status_code == fastapi.status.HTTP_200_OK
    expected_output = {'results': [f'[CSV] - at {tmp_path}/query.csv']}
    assert response.json() == expected_output

  def test_batch_fake_source_from_query_path(self, tmp_path):
    query_path1 = tmp_path / 'query1.sql'
    with pathlib.Path.open(query_path1, 'w', encoding='utf-8') as f:
      f.write(self.query)
    query_path2 = tmp_path / 'query2.sql'
    with pathlib.Path.open(query_path2, 'w', encoding='utf-8') as f:
      f.write(self.query)
    fake_data = _SCRIPT_PATH / 'test.json'
    request = {
      'source': 'fake',
      'query_path': [
        str(query_path1),
        str(query_path2),
      ],
      'context': {
        'fetcher_parameters': {
          'data_location': str(fake_data),
        },
        'writer': 'csv',
        'writer_parameters': {'destination_folder': str(tmp_path)},
      },
    }
    response = client.post('/api/execute:batch', json=request)
    assert response.status_code == fastapi.status.HTTP_200_OK
    expected_output = {
      f'[CSV] - at {tmp_path}/query1.csv',
      f'[CSV] - at {tmp_path}/query2.csv',
    }
    assert set(response.json().get('results')) == expected_output
