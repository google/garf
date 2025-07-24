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

import pytest
import sqlalchemy

from garf_core import report
from garf_executors import sql_executor


class TestSqlAlchemyQueryExecutor:
  @pytest.fixture
  def engine(self):
    return sqlalchemy.create_engine('sqlite:///:memory:')

  @pytest.fixture
  def executor(self, engine):
    return sql_executor.SqlAlchemyQueryExecutor(engine)

  def test_execute_returns_data_saved_to_db(self, executor, engine):
    query = 'CREATE TABLE test AS SELECT 1 AS one;'
    executor.execute(title='test', query=query)

    with engine.connect() as connection:
      result = connection.execute(sqlalchemy.text('select one from test'))
      for row in result:
        assert row.one == 1

  def test_execute_returns_data_to_caller(self, executor):
    query = 'SELECT 1 AS one;'
    expected_result = report.GarfReport(results=[[1]], column_names=['one'])
    result = executor.execute(title='test', query=query)
    assert result == expected_result
