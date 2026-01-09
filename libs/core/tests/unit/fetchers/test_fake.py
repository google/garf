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

from garf.core import report
from garf.core.fetchers import FakeApiReportFetcher


class TestFakeApiReportFetcher:
  data = [
    {'field1': {'subfield': 1}, 'field2': 2},
    {'field1': {'subfield': 10}, 'field2': 2},
  ]

  def test_fetch_from_data_returns_correct_result(self):
    fetcher = FakeApiReportFetcher.from_data(self.data)

    result = fetcher.fetch(
      'SELECT field1.subfield AS column_name FROM resource_name'
    )

    expected_report = report.GarfReport(
      results=[[1], [10]], column_names=['column_name']
    )

    assert result == expected_report

  def test_fetch_from_json_returns_correct_result(self, tmp_path):
    data_location = tmp_path / 'test.json'

    with pathlib.Path.open(data_location, 'w', encoding='utf-8') as f:
      json.dump(self.data, f)
    fetcher = FakeApiReportFetcher.from_json(data_location)

    result = fetcher.fetch(
      'SELECT field1.subfield AS column_name FROM resource_name'
    )

    expected_report = report.GarfReport(
      results=[[1], [10]], column_names=['column_name']
    )

    assert result == expected_report

  def test_fetch_from_csv_returns_correct_result(self, tmp_path):
    data_location = tmp_path / 'test.csv'
    data = [
      {'field1': 1, 'field2': 2},
      {'field1': 10, 'field2': 20},
    ]

    with pathlib.Path.open(data_location, 'w', encoding='utf-8') as f:
      writer = csv.DictWriter(f, fieldnames=['field1', 'field2'])
      writer.writeheader()
      writer.writerows(data)
    fetcher = FakeApiReportFetcher.from_csv(data_location)

    result = fetcher.fetch('SELECT field1 AS column_name FROM resource_name')

    expected_report = report.GarfReport(
      results=[[1], [10]], column_names=['column_name']
    )

    assert result == expected_report
