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

import contextlib
import io
import json
from unittest import mock

import pytest
from garf.community.google.bid_manager import api_clients, query_editor


@pytest.mark.parametrize(
  ('data_range', 'expected'),
  [
    (
      ' = LAST_7_DAYS',
      {'dataRange': {'range': 'LAST_7_DAYS'}},
    ),
    (
      ' IN (2025-01-01, 2025-01-31)',
      {
        'dataRange': {
          'range': 'CUSTOM_DATES',
          'customStartDate': {'year': 2025, 'month': 1, 'day': 1},
          'customEndDate': {'year': 2025, 'month': 1, 'day': 31},
        }
      },
    ),
  ],
)
def test_build_request(data_range, expected):
  query = f"""
    SELECT
    filter_advertiser_name AS advertiser_name,
    advertiser AS advertiser,
    metric_impressions AS impressions,
    FROM standard
    WHERE advertiser = 1
    AND dataRange {data_range}
    """
  spec = query_editor.BidManagerApiQuery(text=query, title='test').generate()

  api_request = api_clients._build_request(spec)

  expected_request = {
    'metadata': {
      'title': 'test',
      'dataRange': expected.get('dataRange'),
      'format': 'CSV',
    },
    'params': {
      'type': 'STANDARD',
      'groupBys': [
        'FILTER_ADVERTISER_NAME',
        'FILTER_ADVERTISER',
      ],
      'filters': [{'type': 'FILTER_ADVERTISER', 'value': '1'}],
      'metrics': [
        'METRIC_IMPRESSIONS',
      ],
    },
    'schedule': {'frequency': 'ONE_TIME'},
  }

  assert api_request == expected_request


def test_process_api_response():
  data = [
    'value1,value2,value3',
    'value1,"value1.5,value2.5",value3',
  ]
  result = api_clients._process_api_response(data, ['one', 'two', 'three'])

  expected_result = [
    {'one': 'value1', 'two': 'value2', 'three': 'value3'},
    {'one': 'value1', 'two': 'value1.5,value2.5', 'three': 'value3'},
  ]

  assert result == expected_result


def _build_query_spec():
  query = """
    SELECT
      advertiser AS advertiser,
      metric_impressions AS impressions
    FROM standard
    WHERE advertiser = 1
    """
  return query_editor.BidManagerApiQuery(text=query, title='test').generate()


def _mock_report_status():
  return {
    'key': {'queryId': '123', 'reportId': '456'},
    'metadata': {
      'status': {'state': 'DONE'},
      'googleCloudStoragePath': 'gs://bucket/report.csv',
    },
  }


def _patch_open(monkeypatch, data: str):
  @contextlib.contextmanager
  def fake_open(*_, **__):
    yield io.StringIO(data)

  monkeypatch.setattr(api_clients.smart_open, 'open', fake_open)


def test_get_response_reuses_cached_report(tmp_path, monkeypatch):
  spec = _build_query_spec()
  cache_file = tmp_path / f'{spec.hash}.txt'
  cache_file.write_text(
    json.dumps({'query_id': '123', 'report_id': '456'}),
    encoding='utf-8',
  )

  client = api_clients.BidManagerApiClient(query_cache_dir=tmp_path)

  mock_client = mock.Mock()
  mock_queries = mock.Mock()
  mock_reports = mock.Mock()
  mock_get_request = mock.Mock()
  mock_get_request.execute.return_value = _mock_report_status()
  mock_reports.get.return_value = mock_get_request
  mock_queries.reports.return_value = mock_reports
  mock_client.queries.return_value = mock_queries
  client._client = mock_client

  _patch_open(monkeypatch, 'col1,col2\nvalue1,value2\n')

  response = client.get_response(spec)

  assert response.results == [
    {'FILTER_ADVERTISER': 'value1', 'METRIC_IMPRESSIONS': 'value2'}
  ]
  mock_queries.create.assert_not_called()
  mock_queries.run.assert_not_called()


def test_get_response_creates_and_caches_report(tmp_path, monkeypatch):
  spec = _build_query_spec()
  client = api_clients.BidManagerApiClient(query_cache_dir=tmp_path)

  mock_client = mock.Mock()
  mock_queries = mock.Mock()
  mock_reports = mock.Mock()

  mock_create = mock.Mock()
  mock_create.execute.return_value = {'queryId': '999'}
  mock_run = mock.Mock()
  mock_run.execute.return_value = {'key': {'queryId': '999', 'reportId': '555'}}
  mock_get_request = mock.Mock()
  mock_get_request.execute.return_value = {
    'key': {'queryId': '999', 'reportId': '555'},
    'metadata': {
      'status': {'state': 'DONE'},
      'googleCloudStoragePath': 'gs://bucket/report.csv',
    },
  }

  mock_reports.get.return_value = mock_get_request
  mock_queries.create.return_value = mock_create
  mock_queries.run.return_value = mock_run
  mock_queries.reports.return_value = mock_reports
  mock_client.queries.return_value = mock_queries
  client._client = mock_client

  _patch_open(monkeypatch, 'col1,col2\nvalue1,value2\n')

  response = client.get_response(spec)

  assert response.results == [
    {'FILTER_ADVERTISER': 'value1', 'METRIC_IMPRESSIONS': 'value2'}
  ]
  mock_queries.create.assert_called_once()
  mock_queries.run.assert_called_once()
  cache_file = tmp_path / f'{spec.hash}.txt'
  assert cache_file.is_file()
  assert json.loads(cache_file.read_text(encoding='utf-8')) == {
    'query_id': '999',
    'report_id': '555',
  }
