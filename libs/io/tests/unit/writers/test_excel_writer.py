# Copyright 2026 Google LLC
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


import pandas as pd
import pytest
from garf.core import report
from garf.io.writers import excel_writer

_TMP_FILENAME = 'test.xlsx'


class TestExcelWriter:
  @pytest.fixture
  def output_folder(self, tmp_path):
    return tmp_path

  def test_write_with_file_writes_to_dedicated_sheet(
    self, single_column_data, output_folder
  ):
    test_writer = excel_writer.ExcelWriter(
      destination_folder=output_folder, file=_TMP_FILENAME
    )
    output = output_folder / _TMP_FILENAME
    result = test_writer.write(single_column_data, destination='test')
    assert f'[Excel] - at {str(output)}' == result

    data = pd.read_excel(output, sheet_name='test')
    assert single_column_data == report.GarfReport.from_pandas(data)

  def test_write_without_file_writes_to_default_sheet(
    self, single_column_data, output_folder
  ):
    test_writer = excel_writer.ExcelWriter(destination_folder=output_folder)
    output = output_folder / 'new_test.xlsx'
    result = test_writer.write(single_column_data, destination='new_test')
    assert f'[Excel] - at {str(output)}' == result

    data = pd.read_excel(output, sheet_name='garf')
    assert single_column_data == report.GarfReport.from_pandas(data)
