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

import pydantic
import pytest
from garf_core import api_clients, parsers, query_editor, query_parser

test_specification = query_editor.QuerySpecification(
  'SELECT test_column_1 FROM test'
).generate()


class NestedResource(pydantic.BaseModel):
  nested_element: int


class ArrayElement(pydantic.BaseModel):
  element: int


class FakeProtoMessage(pydantic.BaseModel):
  resource: str
  resource_id: int
  resource_name: str
  resource_data: NestedResource
  array_data: list[ArrayElement]


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

  @pytest.mark.parametrize(
    ('slice', 'results'),
    [
      (
        '[]',
        ([[1, 2]], [[11, 22]]),
      ),
      (
        '[0]',
        ([[1]], [[11]]),
      ),
      (
        '[0:1]',
        ([[1]], [[11]]),
      ),
      (
        '[1:]',
        ([[2]], [[22]]),
      ),
      (
        '[:1]',
        ([[1]], [[11]]),
      ),
    ],
  )
  def test_parse_response_returns_correct_result_for_arrays(
    self, slice, results
  ):
    spec = query_editor.QuerySpecification(
      f'SELECT test{slice}.element AS column FROM test'
    ).generate()
    test_parser = parsers.DictParser(spec)
    test_response = api_clients.GarfApiResponse(
      results=[
        {'test': [{'element': 1}, {'element': 2}]},
        {'test': [{'element': 11}, {'element': 22}]},
      ]
    )

    parsed_row = test_parser.parse_response(test_response)
    expected_row = list(results)

    assert parsed_row == expected_row

  @pytest.mark.parametrize(
    ('index', 'expected'),
    [
      ('0', [[0], [1]]),
      ('1', [['TEXT'], ['IMAGE']]),
      ('2', [[54321], [12345]]),
    ],
  )
  def test_parse_response_returns_correct_resource_index(self, index, expected):
    spec = query_editor.QuerySpecification(
      text=f'SELECT resource~{index} AS column FROM test'
    ).generate()
    test_parser = parsers.DictParser(spec)
    test_response = api_clients.GarfApiResponse(
      results=[
        {'resource': 'resource/1/test/0~TEXT~54321'},
        {'resource': 'resource/1/test/1~IMAGE~12345'},
      ]
    )
    parsed_row = test_parser.parse_response(test_response)
    assert parsed_row == expected

  def test_parse_response_raises_customizer_error_on_invalid_position(self):
    spec = query_editor.QuerySpecification(
      text='SELECT resource~4 AS column FROM test'
    ).generate()
    test_parser = parsers.DictParser(spec)
    test_response = api_clients.GarfApiResponse(
      results=[
        {'resource': 'resource/1/test/0~TEXT~54321'},
      ]
    )
    with pytest.raises(
      query_parser.GarfCustomizerError, match='Not a valid position in resource'
    ):
      test_parser.parse_response(test_response)

  def test_parse_response_raises_customizer_error_on_invalid_resource(self):
    spec = query_editor.QuerySpecification(
      text='SELECT resource~0 AS column FROM test'
    ).generate()
    test_parser = parsers.DictParser(spec)
    test_response = api_clients.GarfApiResponse(
      results=[
        {'resource': 'resource'},
      ]
    )
    with pytest.raises(
      query_parser.GarfCustomizerError, match='Not a valid resource'
    ):
      test_parser.parse_response(test_response)

  def test_parse_response_skips_omitted_columns(self):
    test_specification = query_editor.QuerySpecification(
      'SELECT test_column_1 AS _, test_column_2 FROM test'
    ).generate()

    test_parser = parsers.DictParser(test_specification)
    test_response = api_clients.GarfApiResponse(
      results=[
        {'test_column_1': '1', 'test_column_2': 2},
        {'test_column_1': '11', 'test_column_2': 22},
      ]
    )

    parsed_row = test_parser.parse_response(test_response)
    expected_row = [[2], [22]]

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


class TestProtoParser:
  @pytest.fixture
  def test_parser(self):
    spec = query_editor.QuerySpecification(
      """
      SELECT
        resource_id,
        resource_id + 1 AS next_resource_id,
        resource_name,
        resource_data.nested_element,
        array_data[0].element AS slice_element
      FROM test
        """
    ).generate()
    return parsers.ProtoParser(spec)

  def test_parse_row_returns_converted_numeric_values(self, test_parser):
    test_row = FakeProtoMessage(
      resource='resources/1/resource/99',
      resource_id=1,
      resource_name='test',
      resource_data=NestedResource(nested_element=10),
      array_data=[ArrayElement(element=100)],
    )

    parsed_row = test_parser.parse_row(test_row)
    expected_row = [1, 2, 'test', 10, [100]]

    assert parsed_row == expected_row

  def test_parse_response_raises_customizer_error_on_missing_nested_attribute(
    self,
  ):
    spec = query_editor.QuerySpecification(
      text='SELECT resource_data:missing_element AS column FROM test'
    ).generate()
    test_parser = parsers.ProtoParser(spec)
    test_response = api_clients.GarfApiResponse(
      results=[
        FakeProtoMessage(
          resource='resources/1/resource/99',
          resource_id=1,
          resource_name='test',
          resource_data=NestedResource(nested_element=10),
          array_data=[ArrayElement(element=100)],
        )
      ]
    )
    with pytest.raises(
      query_parser.GarfCustomizerError,
      match='nested field missing_element is missing in row',
    ):
      test_parser.parse_response(test_response)
