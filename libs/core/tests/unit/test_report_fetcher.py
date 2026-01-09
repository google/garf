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
import logging

import pytest
from garf.core import (
  api_clients,
  parsers,
  report,
  report_fetcher,
)


class TestApiReportFetcher:
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

  def test_fetch_skips_omitted_column(self, test_dict_report_fetcher):
    query = 'SELECT column.name AS _, other_column FROM test'
    test_report = test_dict_report_fetcher.fetch(query)

    expected_report = report.GarfReport(
      results=[[2], [2], [2]],
      column_names=['other_column'],
    )

    assert test_report == expected_report

  def test_fetch_returns_saves_and_loads_cached_version(self, caplog, tmp_path):
    test_api_client = api_clients.FakeApiClient(
      results=[
        {'column': {'name': 1}, 'other_column': 2},
        {'column': {'name': 2}, 'other_column': 2},
        {'column': {'name': 3}, 'other_column': 2},
      ]
    )
    test_fetcher = report_fetcher.ApiReportFetcher(
      api_client=test_api_client,
      parser=parsers.DictParser,
      enable_cache=True,
      cache_path=tmp_path,
    )
    query = 'SELECT column.name, other_column FROM test'
    expected_report = report.GarfReport(
      results=[[1, 2], [2, 2], [3, 2]],
      column_names=['column_name', 'other_column'],
    )

    with caplog.at_level(logging.DEBUG):
      test_report = test_fetcher.fetch(query)
      assert 'Report is saved to cache' in caplog.text
      assert 'Cached version not found, generating' in caplog.text
      assert test_report == expected_report

    with caplog.at_level(logging.DEBUG):
      test_report = test_fetcher.fetch(query)
      assert 'Report is loaded from cache' in caplog.text
      assert 'Cached version of report is loaded' in caplog.text
      assert test_report == expected_report

  def test_fetch_returns_empty_report_for_empty_api_response(self):
    test_api_client = api_clients.FakeApiClient(results=[])
    fetcher = report_fetcher.ApiReportFetcher(
      api_client=test_api_client, parser=parsers.DictParser
    )
    query = 'SELECT column.name, other_column FROM test'
    test_report = fetcher.fetch(query)

    assert not test_report

  @pytest.mark.parametrize(
    ('select', 'expect'),
    [
      ('*', 'test'),
      ('test', 'test'),
      ('test AS new_test', 'new_test'),
    ],
  )
  def test_fetch_builtin_query_returns_correct_builtin_report(
    self, test_dict_report_fetcher, select, expect
  ):
    test_report = report.GarfReport(results=[[1]], column_names=['test'])

    def builtin_query(report_fetcher):
      return test_report

    test_dict_report_fetcher.add_builtin_queries({'test': builtin_query})

    query = f'SELECT {select} FROM builtin.test'
    fetched_report = test_dict_report_fetcher.fetch(query)
    expected_report = report.GarfReport(results=[[1]], column_names=[expect])
    assert fetched_report == expected_report

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

  def test_fetch_returns_results_placeholder_when_missing_results(self):
    test_api_client = api_clients.FakeApiClient(
      results=[],
      results_placeholder=[
        {'column': {'name': 1}, 'other_column': 2},
      ],
    )
    test_fetcher = report_fetcher.ApiReportFetcher(
      api_client=test_api_client, parser=parsers.DictParser
    )

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
    test_report = test_fetcher.fetch(query)

    current_date = datetime.date.today().strftime('%Y-%m-%d')
    expected_report = report.GarfReport(
      results_placeholder=[
        [1, 2, 0, 1 + 2, 'http://example.com/1', current_date],
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

    assert (test_report.results_placeholder, test_report.column_names) == (
      expected_report.results_placeholder,
      expected_report.column_names,
    )
