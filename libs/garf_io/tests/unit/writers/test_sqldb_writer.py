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

import pandas as pd
import pytest

from garf_core import report as garf_report
from garf_io.writers import sqldb_writer

_TMP_NAME = 'test'


class TestSqlAlchemyWriter:
  @pytest.fixture
  def sql_writer(self, tmp_path):
    db_path = tmp_path / 'test.db'
    db_url = f'sqlite:///{db_path}'
    return sqldb_writer.SqlAlchemyWriter(db_url)

  def test_write_single_column_report_returns_correct_data(
    self, sql_writer, single_column_data, tmp_path
  ):
    sql_writer.write(single_column_data, _TMP_NAME)
    df = pd.read_sql(f'SELECT * FROM {_TMP_NAME}', sql_writer.connection_string)

    assert garf_report.GarfReport.from_pandas(df) == single_column_data

  def test_write_multi_column_report_with_arrays_returns_concatenated_strings(
    self, sql_writer, sample_data
  ):
    results = [[1, 'two', '3|4']]
    columns = ['column_1', 'column_2', 'column_3']
    expected_report = garf_report.GarfReport(results, columns)

    sql_writer.array_handling = 'strings'
    sql_writer.write(sample_data, _TMP_NAME)

    df = pd.read_sql(f'SELECT * FROM {_TMP_NAME}', sql_writer.connection_string)

    assert garf_report.GarfReport.from_pandas(df) == expected_report
