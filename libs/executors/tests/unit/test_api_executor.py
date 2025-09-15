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
# limitations under the License
from __future__ import annotations

import json
import pathlib

import pytest
from garf_core import api_clients, parsers, report_fetcher
from garf_core.fetchers import fake as fake_fetcher
from garf_executors import api_executor
from garf_io.writers import json_writer

_TEST_DATA = [
  {'customer_id': 1},
  {'customer_id': 2},
  {'customer_id': 3},
]

_TEST_QUERY = 'SELECT customer.id FROM customer'


class TestApiQueryExecutor:
  @pytest.fixture
  def executor(self):
    test_api_client = api_clients.FakeApiClient(
      results=[
        {'customer': {'id': 1}},
        {'customer': {'id': 2}},
        {'customer': {'id': 3}},
      ]
    )
    test_fetcher = report_fetcher.ApiReportFetcher(
      api_client=test_api_client, parser=parsers.DictParser
    )
    return api_executor.ApiQueryExecutor(test_fetcher)

  @pytest.fixture
  def test_json_writer(self, tmp_path):
    return json_writer.JsonWriter(destination_folder=tmp_path)

  def test_execute_returns_success(self, executor, tmp_path):
    context = api_executor.ApiExecutionContext(
      writer='json',
      writer_parameters={'destination_folder': str(tmp_path)},
    )
    executor.execute(
      query=_TEST_QUERY,
      title='test',
      context=context,
    )
    with pathlib.Path.open(
      pathlib.Path(context.writer_client.destination_folder) / 'test.json',
      'r',
      encoding='utf-8',
    ) as f:
      result = json.load(f)

    assert result == _TEST_DATA

  def test_from_fetcher_alias_returns_initialized_executor(self, tmp_path):
    tmp_file = tmp_path / 'test.json'
    with pathlib.Path.open(
      tmp_file,
      'w',
      encoding='utf-8',
    ) as f:
      json.dump(_TEST_DATA, f)

    executor = api_executor.ApiQueryExecutor.from_fetcher_alias(
      source='fake',
      fetcher_parameters={
        'json_location': tmp_file,
      },
    )
    assert isinstance(executor.fetcher, fake_fetcher.FakeApiReportFetcher)
