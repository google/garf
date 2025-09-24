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


import datetime

import pytest
from garf_core import (
  api_clients,
  parsers,
  report,
  report_fetcher,
)


class TestApiReportFetcher:
  @pytest.fixture
  def test_list_report_fetcher(self):
    test_api_client = api_clients.FakeApiClient(results=[[1], [2], [3]])
    return report_fetcher.ApiReportFetcher(
      api_client=test_api_client, parser=parsers.ListParser
    )

  @pytest.fixture
  def test_dict_report_fetcher(self):
    test_api_client = api_clients.FakeApiClient(
      results=[
        {'column': {'name': 1}, 'other_column': 2},
        {'column': {'name': 2}, 'other_column': 2},
        {'column': {'name': 3}, 'other_column': 2},
      ]
    )
    return report_fetcher.ApiReportFetcher(
      api_client=test_api_client, parser=parsers.DictParser
    )

  def test_fetch_returns_correct_report_for_list_parser(
    self, test_list_report_fetcher
  ):
    query = 'SELECT column as column_name FROM test'
    test_report = test_list_report_fetcher.fetch(query)

    expected_report = report.GarfReport(
      results=[[1], [2], [3]],
      column_names=['column_name'],
    )

    assert test_report == expected_report

  def test_fetch_returns_correct_report_for_dict_parser(
    self, test_dict_report_fetcher
  ):
    query = 'SELECT column.name, other_column FROM test'
    test_report = test_dict_report_fetcher.fetch(query)

    expected_report = report.GarfReport(
      results=[[1, 2], [2, 2], [3, 2]],
      column_names=['column_name', 'other_column'],
    )

    assert test_report == expected_report

  def test_fetch_builtin_query_returns_correct_builtin_report(
    self, test_dict_report_fetcher
  ):
    test_report = report.GarfReport(results=[[1]], column_names=['test'])

    def test_builtin_query(report_fetcher):
      return test_report

    test_dict_report_fetcher.add_builtin_queries({'test': test_builtin_query})

    query = 'SELECT test FROM builtin.test'
    fetched_report = test_dict_report_fetcher.fetch(query)

    assert fetched_report == test_report

  def test_fetch_parses_virtual_columns(self, test_dict_report_fetcher):
    query = """
      SELECT
        column.name,
        other_column,
        0 AS constant_column,
        column.name + other_column AS calculated_column,
        'http://example.com/' + column.name AS concat_column,
        '{current_date}' AS magic_column
      FROM test
    """
    test_report = test_dict_report_fetcher.fetch(query)

    current_date = datetime.date.today().strftime('%Y-%m-%d')
    expected_report = report.GarfReport(
      results=[
        [1, 2, 0, 1 + 2, 'http://example.com/1', current_date],
        [2, 2, 0, 2 + 2, 'http://example.com/2', current_date],
        [3, 2, 0, 3 + 2, 'http://example.com/3', current_date],
      ],
      column_names=[
        'column_name',
        'other_column',
        'constant_column',
        'calculated_column',
        'concat_column',
        'magic_column',
      ],
    )

    assert test_report == expected_report
