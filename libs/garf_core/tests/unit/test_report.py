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
from __future__ import annotations

import json
from collections import abc

import pandas as pd
import polars as pl
import pytest

from garf_core import report


@pytest.fixture
def empty_report():
  return report.GarfReport()


@pytest.fixture
def single_element_report():
  return report.GarfReport(results=[[1]], column_names=['campaign_id'])


@pytest.fixture
def single_column_report():
  return report.GarfReport(
    results=[[1], [1], [3]], column_names=['campaign_id']
  )


@pytest.fixture
def multi_column_report():
  return report.GarfReport(
    results=[[1, 2], [2, 3], [3, 4]],
    column_names=['campaign_id', 'ad_group_id'],
  )


class TestGarfReport:
  class TestGarfReportIteration:
    def test_empty_report_returns_empty_list(self, empty_report):
      assert list(empty_report) == []

    def test_single_element_report_returns_garf_row(
      self, single_element_report
    ):
      assert [row[0] for row in single_element_report] == [1]

    def test_single_column_report_returns_sequence(self, single_column_report):
      assert [row[0] for row in single_column_report] == [1, 1, 3]

    def test_multi_column_report_returns_garf_row(self, multi_column_report):
      assert isinstance(list(multi_column_report)[0], report.GarfRow)

    def test_multi_column_report_support_iteration_with_garf_iterator(
      self,
      multi_column_report,
    ):
      assert isinstance(iter(multi_column_report), abc.Iterable)

    def test_multi_column_report_get_element_by_id(self, multi_column_report):
      assert [row[0] for row in multi_column_report] == [1, 2, 3]

    def test_multi_column_report_get_element_by_name(self, multi_column_report):
      assert [row['campaign_id'] for row in multi_column_report] == [1, 2, 3]

    def test_multi_column_report_get_element_with_get_method(
      self, multi_column_report
    ):
      assert [row.get('campaign_id') for row in multi_column_report] == [
        1,
        2,
        3,
      ]

    def test_multi_column_report_get_element_as_attribute(
      self, multi_column_report
    ):
      assert [row.campaign_id for row in multi_column_report] == [1, 2, 3]

    def test_getitem_raise_index_error_for_out_of_index_value(
      self,
      multi_column_report,
    ):
      with pytest.raises(report.GarfReportError):
        [row[99] for row in multi_column_report] == [1, 2, 3]

    def test_get_raises_attribute_error_for_missing_value(
      self, multi_column_report
    ):
      with pytest.raises(AttributeError):
        [row.get('missing_value') for row in multi_column_report] == [
          None,
          None,
          None,
        ]

    def test_getattr_raises_attribute_error_for_missing_value(
      self,
      multi_column_report,
    ):
      with pytest.raises(AttributeError):
        [getattr(row, 'missing_value') for row in multi_column_report] == [
          None,
          None,
          None,
        ]

    def test_hasattr_return_false_for_missing_value(self, multi_column_report):
      assert [hasattr(row, 'missing_value') for row in multi_column_report] == [
        False,
        False,
        False,
      ]

  class TestGarfReportMisc:
    def test_empty_report_length(self, empty_report):
      assert len(empty_report) == 0

    def test_get_report_length(self, multi_column_report):
      assert len(multi_column_report) == len(multi_column_report.results)

    def test_report_bool(self, single_element_report):
      assert single_element_report
      single_element_report.results = []
      assert not single_element_report

    def test_empty_report_bool_return_false(self, empty_report):
      assert not empty_report

  class TestGarfReportAddition:
    def test_add_two_empty_reports(self, empty_report):
      added_report = empty_report + empty_report
      assert len(added_report) == 0

    def test_add_two_reports(self, multi_column_report):
      added_report = multi_column_report + multi_column_report
      assert len(added_report) == len(multi_column_report.results) * 2

    def test_add_report_and_non_report_raises_exception(
      self, multi_column_report
    ):
      with pytest.raises(report.GarfReportError):
        multi_column_report + 1

    def test_add_non_report_and_report_raises_exception(
      self, multi_column_report
    ):
      with pytest.raises(TypeError):
        1 + multi_column_report

    def test_add_reports_with_different_columns_raises_exception(
      self, multi_column_report, single_element_report
    ):
      with pytest.raises(report.GarfReportError):
        multi_column_report + single_element_report

  class TestGarfReportSlicing:
    def test_slicing_empty_garf_report_returns_empty_list(
      self,
      empty_report,
    ):
      with pytest.raises(
        report.GarfReportError, match='Cannot get element from an empty report'
      ):
        empty_report[0:2]

    def test_slicing_multi_column_garf_report_returns_garf_report(
      self,
      multi_column_report,
    ):
      new_report = multi_column_report[0:2]
      assert new_report == report.GarfReport(
        results=[[1, 2], [2, 3]], column_names=['campaign_id', 'ad_group_id']
      )

    def test_indexing_multi_column_garf_report_by_single_index_returns_garf_row(
      self,
      multi_column_report,
    ):
      new_report = multi_column_report[0]
      assert new_report == report.GarfRow(
        data=[1, 2], column_names=['campaign_id', 'ad_group_id']
      )

    def test_indexing_multi_column_garf_report_by_multi_index_returns_garf_report(
      self,
      multi_column_report,
    ):
      new_report = multi_column_report[0:2]
      assert new_report == report.GarfReport(
        results=[[1, 2], [2, 3]], column_names=['campaign_id', 'ad_group_id']
      )

    def test_indexing_empty_garf_report_by_one_column_returns_garf_report(
      self,
      empty_report,
    ):
      with pytest.raises(
        report.GarfReportError,
        match="Cannot get 'campaign_id' from an empty report",
      ):
        empty_report['campaign_id']

    def test_indexing_multi_column_garf_report_by_one_column_returns_garf_report(
      self,
      multi_column_report,
    ):
      new_report = multi_column_report['campaign_id']
      assert new_report == report.GarfReport(
        results=[[1], [2], [3]], column_names=['campaign_id']
      )

    def test_indexing_multi_column_garf_report_by_several_columns_returns_garf_report(
      self,
      multi_column_report,
    ):
      new_report = multi_column_report[['campaign_id', 'ad_group_id']]
      assert new_report == multi_column_report

    def test_indexing_multi_column_garf_report_by_non_existing_column_raises_garf_report_error(
      self,
      multi_column_report,
    ):
      with pytest.raises(
        report.GarfReportError,
        match="Columns 'ad_group' cannot be found in the report",
      ):
        multi_column_report[['campaign_id', 'ad_group']]

    def test_slicing_single_column_garf_report_returns_report(
      self,
      single_column_report,
    ):
      single_column_report.disable_scalar_conversions()
      new_report = single_column_report[0:2]
      expected_report = report.GarfReport(
        results=[[1], [1]], column_names=['campaign_id']
      )
      assert new_report == expected_report

    def test_slicing_single_column_garf_report_returns_row(
      self,
      single_column_report,
    ):
      single_column_report.disable_scalar_conversions()
      row = single_column_report[0]
      expected_row = report.GarfRow(data=[1], column_names=['campaign_id'])
      assert row == expected_row

    def test_slicing_single_column_garf_report_returns_slice(
      self,
      single_column_report,
    ):
      with pytest.warns(FutureWarning) as w:
        result = single_column_report[0:2]
        assert result == [1, 1]
        assert len(w) == 1
        assert str(w[0].message) == (
          'Getting scalars from single column `GarfReport` is discouraged and '
          'will be deprecated in future releases of garf. To get scalar value '
          'use `get_value()` method instead. '
          'Call `.disable_scalar_conversions()` to return GarfRow '
          'or GarfReport.'
        )

    def test_slicing_single_column_garf_report_returns_element(
      self,
      single_column_report,
    ):
      with pytest.warns(FutureWarning) as w:
        result = single_column_report[0]
        assert result == [1]
        assert len(w) == 1
        assert str(w[0].message) == (
          'Getting scalars from single column `GarfReport` is discouraged and '
          'will be deprecated in future releases of garf. To get scalar value '
          'use `get_value()` method instead. '
          'Call `.disable_scalar_conversions()` to return GarfRow '
          'or GarfReport.'
        )

    def test_set_existing_attribute_garf_multiple_rows_updates_columns(
      self,
      multi_column_report,
    ):
      for row in multi_column_report:
        row.campaign_id = row.campaign_id * 100
      assert multi_column_report == report.GarfReport(
        results=[[100, 2], [200, 3], [300, 4]],
        column_names=['campaign_id', 'ad_group_id'],
      )

    def test_set_non_existing_attribute_garf_rows_get_new_columns(
      self,
      multi_column_report,
    ):
      for row in multi_column_report:
        row.campaign_id_new = row.campaign_id * 100
      assert multi_column_report == report.GarfReport(
        results=[[1, 2, 100], [2, 3, 200], [3, 4, 300]],
        column_names=['campaign_id', 'ad_group_id', 'campaign_id_new'],
      )

  class TestGarfReportConversions:
    def test_single_column_report_returns_flattened_list(
      self, single_column_report
    ):
      assert single_column_report.to_list() == [1, 1, 3]

    def test_single_column_report_returns_distinct_flattened_list(
      self,
      single_column_report,
    ):
      assert single_column_report.to_list(row_type='scalar', distinct=True) == [
        1,
        3,
      ]

    def test_single_column_report_returns_distinct_flattened_list_legacy(
      self,
      single_column_report,
    ):
      assert single_column_report.to_list(flatten=True, distinct=True) == [1, 3]

    def test_multi_column_report_converted_to_dict_list_values(
      self,
      multi_column_report,
    ):
      key_column = 'campaign_id'
      value_column = 'ad_group_id'
      output_dict = multi_column_report.to_dict(
        key_column=key_column, value_column=value_column
      )
      assert output_dict == {1: [2], 2: [3], 3: [4]}

    def test_multi_column_report_converted_to_dict_scalar_values(
      self,
      multi_column_report,
    ):
      key_column = 'campaign_id'
      value_column = 'ad_group_id'
      output_dict = multi_column_report.to_dict(
        key_column=key_column,
        value_column=value_column,
        value_column_output='scalar',
      )
      assert output_dict == {1: 2, 2: 3, 3: 4}

    def test_multi_column_report_with_duplicates_converted_to_dict_scalar_returns_unique_values(
      self,
    ):
      multi_column_report = report.GarfReport(
        results=[[1, 2], [2, 3], [3, 4], [3, 4]],
        column_names=['campaign_id', 'ad_group_id'],
      )
      key_column = 'campaign_id'
      value_column = 'ad_group_id'
      output_dict = multi_column_report.to_dict(
        key_column=key_column,
        value_column=value_column,
        value_column_output='scalar',
      )
      assert output_dict == {1: 2, 2: 3, 3: 4}

    def test_multi_column_report_converted_to_dict_raises_exception_on_non_existing_key_column(
      self,
      multi_column_report,
    ):
      key_column = 'missing_column'
      value_column = 'ad_group_id'
      with pytest.raises(report.GarfReportError):
        multi_column_report.to_dict(
          key_column=key_column,
          value_column=value_column,
          value_column_output='scalar',
        )

    def test_multi_column_report_converted_to_dict_raises_exception_on_non_existing_value_column(
      self,
      multi_column_report,
    ):
      key_column = 'campaign_id'
      value_column = 'missing_column'
      with pytest.raises(report.GarfReportError):
        multi_column_report.to_dict(
          key_column=key_column,
          value_column=value_column,
          value_column_output='scalar',
        )

    def test_multi_column_report_converted_to_dict_with_missing_value_column(
      self,
      multi_column_report,
    ):
      key_column = 'campaign_id'
      output_dict = multi_column_report.to_dict(key_column=key_column)
      assert output_dict == {
        1: [{'campaign_id': 1, 'ad_group_id': 2}],
        2: [{'campaign_id': 2, 'ad_group_id': 3}],
        3: [{'campaign_id': 3, 'ad_group_id': 4}],
      }

    def test_multi_column_report_converted_to_dict_without_arguments(
      self,
      multi_column_report,
    ):
      output_dict = multi_column_report.to_list(row_type='dict')
      assert output_dict == [
        {'campaign_id': 1, 'ad_group_id': 2},
        {'campaign_id': 2, 'ad_group_id': 3},
        {'campaign_id': 3, 'ad_group_id': 4},
      ]

    def test_to_list_incorrect_row_type_raises_exception(
      self, multi_column_report
    ):
      with pytest.raises(report.GarfReportError):
        multi_column_report.to_list(row_type='tuple')

    def test_empty_report_converted_to_dict_with_key_column(
      self, multi_column_report
    ):
      key_column = 'campaign_id'
      value_column = 'ad_group_id'
      # clear results of report
      multi_column_report.results = []
      output_dict = multi_column_report.to_dict(
        key_column=key_column,
        value_column=value_column,
        value_column_output='scalar',
      )
      assert output_dict == {key_column: None}

    def test_multi_column_report_converted_to_json(
      self,
      multi_column_report,
    ):
      output_json = multi_column_report.to_json()
      assert json.loads(output_json) == [
        {'campaign_id': 1, 'ad_group_id': 2},
        {'campaign_id': 2, 'ad_group_id': 3},
        {'campaign_id': 3, 'ad_group_id': 4},
      ]

    def test_multi_column_report_converted_to_json_with_jsonl_output(
      self,
      multi_column_report,
    ):
      output_json = multi_column_report.to_json(output='jsonl')
      expected_rows = [
        {'campaign_id': 1, 'ad_group_id': 2},
        {'campaign_id': 2, 'ad_group_id': 3},
        {'campaign_id': 3, 'ad_group_id': 4},
      ]
      for i, json_str in enumerate(output_json.split('\n')):
        assert json.loads(json_str) == expected_rows[i]

    def test_multi_column_report_converted_to_jsonl(
      self,
      multi_column_report,
    ):
      output_json = multi_column_report.to_jsonl()
      expected_rows = [
        {'campaign_id': 1, 'ad_group_id': 2},
        {'campaign_id': 2, 'ad_group_id': 3},
        {'campaign_id': 3, 'ad_group_id': 4},
      ]
      for i, json_str in enumerate(output_json.split('\n')):
        assert json.loads(json_str) == expected_rows[i]

    def test_conversion_from_pandas(
      self,
    ):
      values = [[1, 2], [3, 4]]
      column_names = ['one', 'two']
      df = pd.DataFrame(data=values, columns=column_names)
      report_from_df = report.GarfReport.from_pandas(df)
      expected_report = report.GarfReport(
        results=values, column_names=column_names
      )
      assert report_from_df == expected_report

    def test_conversion_from_polars(
      self,
    ):
      values = [[1, 2], [3, 4]]
      column_names = ['one', 'two']
      df = pl.DataFrame(data=values, schema=column_names, orient='row')
      report_from_df = report.GarfReport.from_polars(df)
      expected_report = report.GarfReport(
        results=values, column_names=column_names
      )
      assert report_from_df == expected_report

    def test_from_json_with_single_row_dict_returns_gaarf_report(self):
      json_str = '{"ad_group_id": 2, "campaign_id": 1}'
      gaarf_report = report.GarfReport.from_json(json_str)
      expected_report = report.GarfReport(
        results=[[2, 1]], column_names=['ad_group_id', 'campaign_id']
      )
      assert gaarf_report == expected_report

    def test_from_json_with_list_of_dicts_returns_gaarf_report(self):
      json_str = (
        '[{"ad_group_id": 2, "campaign_id": 1}, {"ad_group_id": 3, '
        '"campaign_id": 2}]'
      )
      gaarf_report = report.GarfReport.from_json(json_str)
      expected_report = report.GarfReport(
        results=[[2, 1], [3, 2]], column_names=['ad_group_id', 'campaign_id']
      )
      assert gaarf_report == expected_report

    def test_from_json_with_empty_list_returns_empty_report(self):
      json_str = '[]'
      gaarf_report = report.GarfReport.from_json(json_str)
      expected_report = report.GarfReport(results=[], column_names=[])
      assert gaarf_report == expected_report

    def test_from_json_with_empty_dict_returns_empty_report(self):
      json_str = '{}'
      gaarf_report = report.GarfReport.from_json(json_str)
      expected_report = report.GarfReport(results=[], column_names=[])
      assert gaarf_report == expected_report

    def test_from_json_with_inconsistent_keys_raises_value_error(self):
      json_str = '[{"ad_group_id": 2}, {"campaign_id": 1}]'
      with pytest.raises(
        ValueError,
        match='All dictionaries must have consistent keys in the same order.',
      ):
        report.GarfReport.from_json(json_str)

    def test_from_json_with_unsupported_type_in_dict_raises_type_error(self):
      json_str = '{"ad_group_id": {"nested": "value"}, "campaign_id": 1}'
      with pytest.raises(
        TypeError, match=r"Unsupported type <class 'dict'> for value"
      ):
        report.GarfReport.from_json(json_str)

    def test_from_json_with_unsupported_type_in_list_raises_type_error(self):
      json_str = (
        '[{"ad_group_id": 2, "campaign_id": {"ad_group_id": 2, '
        '"campaign_id": 1}}]'
      )
      with pytest.raises(
        TypeError,
        match=r"Unsupported type <class 'dict'> for value {'ad_group_id': 2, "
        r"'campaign_id': 1}. Expected types: int, float, str, bool, list, or "
        r'None.',
      ):
        report.GarfReport.from_json(json_str)

    def test_from_json_with_inconsistent_column_order_raises_value_error(self):
      json_str = (
        '[{"ad_group_id": 2, "campaign_id": 1}, {"campaign_id": 2, '
        '"ad_group_id": 3}]'
      )

      with pytest.raises(
        ValueError,
        match='All dictionaries must have consistent keys in the same order.',
      ):
        report.GarfReport.from_json(json_str)

    def test_from_json_with_non_dict_or_list_raises_type_error(self):
      json_str = '"invalid_data"'
      with pytest.raises(
        TypeError,
        match='Input JSON must be a dictionary or a list of dictionaries.',
      ):
        report.GarfReport.from_json(json_str)

    def test_from_json_with_non_dict_elements_in_list_raises_type_error(self):
      json_str = '[{"ad_group_id": 2}, 123]'
      with pytest.raises(
        TypeError, match='All elements in the list must be dictionaries.'
      ):
        report.GarfReport.from_json(json_str)

    def test_convert_empty_report_to_pandas_returns_empty_dataframe(
      self, empty_report
    ):
      expected = pd.DataFrame()
      assert empty_report.to_pandas().equals(expected)

    def test_convert_report_to_pandas(self, multi_column_report):
      expected = pd.DataFrame(
        data=[[1, 2], [2, 3], [3, 4]], columns=['campaign_id', 'ad_group_id']
      )
      assert multi_column_report.to_pandas().equals(expected)

    def test_convert_empty_report_to_polars_returns_empty_dataframe(
      self, empty_report
    ):
      expected = pl.DataFrame()
      assert empty_report.to_polars().equals(expected)

    def test_convert_report_to_polars(self, multi_column_report):
      expected = pl.DataFrame(
        data=[[1, 2], [2, 3], [3, 4]], schema=['campaign_id', 'ad_group_id']
      )
      assert multi_column_report.to_polars().equals(expected)

    def test_get_value_empty_report_raises_garf_report_error(
      self,
      empty_report,
    ):
      with pytest.raises(
        report.GarfReportError, match='Cannot get value from an empty report'
      ):
        empty_report.get_value()

    def test_get_value_single_element_report_returns_correct_value(
      self,
      single_element_report,
    ):
      assert single_element_report.get_value() == 1

    def test_get_value_multi_column_report_returns_index_position(
      self,
      multi_column_report,
    ):
      assert (
        multi_column_report.get_value(column_index=1, row_index=1)
        == multi_column_report[1][1]
      )

    def test_get_value_raises_exception_when_column_index_out_of_bound(
      self,
      single_element_report,
    ):
      with pytest.raises(report.GarfReportError):
        single_element_report.get_value(column_index=1)

    def test_get_value_raises_exception_when_row_index_out_of_bound(
      self,
      single_element_report,
    ):
      with pytest.raises(report.GarfReportError):
        single_element_report.get_value(row_index=1)

  class TestGarfReportEquality:
    def test_empty_reports_are_equal(self):
      assert report.GarfReport() == report.GarfReport()

    def test_report_with_different_columns_not_equal(
      self, single_element_report, multi_column_report
    ):
      assert single_element_report != multi_column_report

    def test_report_with_different_data_are_not_equal(
      self, multi_column_report
    ):
      new_multi_column_report = report.GarfReport(
        results=list(multi_column_report.results),
        column_names=list(multi_column_report.column_names),
      )
      new_multi_column_report.results[0] = [10, 10]
      assert new_multi_column_report != multi_column_report

    def test_report_with_same_data_are_equal(self, multi_column_report):
      new_multi_column_report = report.GarfReport(
        results=list(multi_column_report.results),
        column_names=list(multi_column_report.column_names),
      )
      assert new_multi_column_report == multi_column_report

    def test_report_with_same_data_different_order_are_equal(
      self, multi_column_report
    ):
      new_multi_column_report = report.GarfReport(
        results=[[2, 1], [3, 2], [4, 3]],
        column_names=['ad_group_id', 'campaign_id'],
      )
      assert new_multi_column_report == multi_column_report


class TestGarfRow:
  @pytest.fixture
  def test_row(self, multi_column_report):
    return multi_column_report[0]

  def test_set_non_existing_item_garf_row_get_new_column(self, test_row):
    test_row['campaign_id_new'] = test_row['campaign_id'] * 100
    assert test_row == report.GarfRow(
      data=[1, 2, 100],
      column_names=['campaign_id', 'ad_group_id', 'campaign_id_new'],
    )

  def test_set_existing_item_garf_row_updates_column(self, test_row):
    test_row['campaign_id'] = test_row['campaign_id'] * 100
    assert test_row == report.GarfRow(
      data=[100, 2], column_names=['campaign_id', 'ad_group_id']
    )

  def test_set_non_existing_attribute_garf_test_row_get_new_column(
    self,
    test_row,
  ):
    test_row.campaign_id_new = test_row.campaign_id * 100
    assert test_row == report.GarfRow(
      data=[1, 2, 100],
      column_names=['campaign_id', 'ad_group_id', 'campaign_id_new'],
    )

  def test_set_existing_attribute_garf_test_row_updates_column(self, test_row):
    test_row.campaign_id = test_row.campaign_id * 100
    assert test_row == report.GarfRow(
      data=[100, 2], column_names=['campaign_id', 'ad_group_id']
    )
