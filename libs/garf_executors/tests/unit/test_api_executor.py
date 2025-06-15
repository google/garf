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
import os

import pytest

from garf_core import api_clients, parsers, report_fetcher
from garf_executors import api_executor
from garf_io.writers import json_writer


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
    query_text = 'SELECT customer.id FROM customer'
    expected_result = [
      {'customer_id': 1},
      {'customer_id': 2},
      {'customer_id': 3},
    ]

    context = api_executor.ApiExecutionContext(
      writer='json',
      writer_parameters={'destination_folder': str(tmp_path)},
    )
    executor.execute(
      query=query_text,
      title='test',
      context=context,
    )
    with open(
      os.path.join(context.writer_client.destination_folder, 'test.json'),
      'r',
      encoding='utf-8',
    ) as f:
      result = json.load(f)

    assert result == expected_result
