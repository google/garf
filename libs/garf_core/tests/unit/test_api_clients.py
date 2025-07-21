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

import csv
import json
import pathlib

import pytest

from garf_core import api_clients


class TestFakeApiClient:
  def test_from_csv_returns_correct_results(self, tmp_path):
    data = [
      {'field1': 1, 'field2': 2},
      {'field1': 10, 'field2': 20},
    ]
    tmp_file = tmp_path / 'test.csv'

    with pathlib.Path.open(tmp_file, 'w', encoding='utf-8') as f:
      writer = csv.DictWriter(f, fieldnames=['field1', 'field2'])
      writer.writeheader()
      writer.writerows(data)

    api_client = api_clients.FakeApiClient.from_csv(tmp_file)

    assert api_client.results == data

  def test_from_json_returns_correct_results(self, tmp_path):
    data = [
      {'field1': {'subfield1': 1}, 'field2': 2},
      {'field1': {'subfield1': 10}, 'field2': 2},
    ]
    tmp_file = tmp_path / 'test.json'

    with pathlib.Path.open(tmp_file, 'w', encoding='utf-8') as f:
      json.dump(data, f)

    api_client = api_clients.FakeApiClient.from_json(tmp_file)

    assert api_client.results == data

  def test_from_file_returns_correct_results(self, tmp_path):
    data = [
      {'field1': {'subfield1': 1}, 'field2': 2},
      {'field1': {'subfield1': 10}, 'field2': 2},
    ]
    tmp_file = tmp_path / 'test.json'

    with pathlib.Path.open(tmp_file, 'w', encoding='utf-8') as f:
      json.dump(data, f)

    api_client = api_clients.FakeApiClient.from_file(tmp_file)

    assert api_client.results == data

  def test_from_file_raises_garf_api_error_on_missing_file(self):
    with pytest.raises(api_clients.GarfApiError, match='Failed to open'):
      api_clients.FakeApiClient.from_file('not-existing.csv')

  def test_from_file_raises_garf_api_error_on_unsupported_file_extension(self):
    with pytest.raises(
      api_clients.GarfApiError, match='Unsupported file extension'
    ):
      api_clients.FakeApiClient.from_file('not-existing.yaml')
