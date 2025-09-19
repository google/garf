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

import pytest
from garf_core import api_clients, parsers, query_editor

test_specification = query_editor.QuerySpecification(
  'SELECT test_column_1 FROM test'
).generate()


class TestDictParser:
  @pytest.fixture
  def test_parser(self):
    return parsers.DictParser(test_specification)

  def test_parse_row_returns_correct_result(self, test_parser):
    test_row = {'test_column_1': '1', 'test_column_2': 2}

    parsed_row = test_parser.parse_row(test_row)
    expected_row = ['1']

    assert parsed_row == expected_row

  def test_parse_response_returns_correct_result(self, test_parser):
    test_response = api_clients.GarfApiResponse(
      results=[
        {'test_column_1': '1', 'test_column_2': 2},
        {'test_column_1': '11', 'test_column_2': 22},
      ]
    )

    parsed_row = test_parser.parse_response(test_response)
    expected_row = [['1'], ['11']]

    assert parsed_row == expected_row

  def test_parse_response_returns_empty_list_on_missing_results(
    self, test_parser
  ):
    test_response = api_clients.GarfApiResponse(results=[])

    parsed_row = test_parser.parse_response(test_response)
    expected_row = [[]]

    assert parsed_row == expected_row

  def test_parse_response_raises_garf_parse_error_on_incorrect_items(
    self, test_parser
  ):
    test_response = api_clients.GarfApiResponse(results=[[1, 2]])

    with pytest.raises(parsers.GarfParserError):
      test_parser.parse_response(test_response)

  def test_parse_response_returns_none_for_missing_field(self):
    test_specification = query_editor.QuerySpecification(
      'SELECT test_column_1, missing_column.field FROM test'
    ).generate()
    parser = parsers.DictParser(test_specification)
    test_response = api_clients.GarfApiResponse(
      results=[
        {'test_column_1': '1', 'test_column_2': 2},
        {'test_column_1': '11', 'test_column_2': 22},
      ]
    )

    parsed_row = parser.parse_response(test_response)
    expected_row = [['1', None], ['11', None]]

    assert parsed_row == expected_row


class TestNumericDictParser:
  @pytest.fixture
  def test_parser(self):
    return parsers.NumericConverterDictParser(test_specification)

  def test_parse_row_returns_converted_numeric_values(self, test_parser):
    test_row = {'test_column_1': '1', 'test_column_2': 2}

    parsed_row = test_parser.parse_row(test_row)
    expected_row = [1]

    assert parsed_row == expected_row


class TestListParser:
  @pytest.fixture
  def test_parser(self):
    return parsers.ListParser(test_specification)

  def test_parse_row_returns_converted_numeric_values(self, test_parser):
    test_row = {'test_column_1': '1', 'test_column_2': 2}

    parsed_row = test_parser.parse_row(test_row)

    assert parsed_row == test_row
