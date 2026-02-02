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

import pytest
import sqlalchemy
from garf.core import query_editor, report
from garf.executors import execution_context, sql_executor
from garf.io import writer


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

  def test_execute_works_with_multiple_tables(self, executor, engine):
    query = """
    CREATE TABLE test1 AS SELECT 1 AS one;
    CREATE TABLE test2 AS SELECT 2 AS one;
    """
    executor.execute(title='test', query=query)

    with engine.connect() as connection:
      result = connection.execute(sqlalchemy.text('select one from test1'))
      for row in result:
        assert row.one == 1

      result = connection.execute(sqlalchemy.text('select one from test2'))
      for row in result:
        assert row.one == 2

  def test_execute_returns_data_to_caller(self, executor):
    query = 'SELECT 1 AS one;'
    expected_result = report.GarfReport(results=[[1]], column_names=['one'])
    result = executor.execute(title='test', query=query)
    assert result == expected_result

  def test_execute_writers_data_via_executor_writer(self, engine, tmp_path):
    writers = writer.setup_writers(
      writers=['json'], writer_parameters={'destination_folder': tmp_path}
    )
    executor = sql_executor.SqlAlchemyQueryExecutor(
      engine=engine, writers=writers
    )
    query = 'SELECT 1 AS one;'
    result = executor.execute(
      title='test',
      query=query,
    )
    output_path = str(tmp_path / 'test.json')
    assert result == f'[JSON] - at {output_path}'
    with open(output_path, 'r', encoding='utf-8') as f:
      data = json.load(f)
    assert data == [{'one': 1}]

  def test_execute_writers_data_via_context_writer(self, engine, tmp_path):
    executor = sql_executor.SqlAlchemyQueryExecutor(engine=engine)
    query = 'SELECT 1 AS one;'
    result = executor.execute(
      title='test',
      query=query,
      context=execution_context.ExecutionContext(
        writer='json', writer_parameters={'destination_folder': str(tmp_path)}
      ),
    )
    output_path = str(tmp_path / 'test.json')
    assert result == f'[JSON] - at {output_path}'
    with open(output_path, 'r', encoding='utf-8') as f:
      data = json.load(f)
    assert data == [{'one': 1}]

  @pytest.mark.parametrize(
    ('selective', 'expected'), [(None, 2), ('true', 1), ('false', 2)]
  )
  def test_execute_handles_templates(self, executor, selective, expected):
    query = """
    SELECT
      {% if selective == "true" %}
        1 AS field
      {% else %}
        2 AS field
      {% endif %}
    ;
    """
    expected_result = report.GarfReport(
      results=[[expected]], column_names=['field']
    )
    if selective is None:
      context = execution_context.ExecutionContext()
    else:
      context = execution_context.ExecutionContext(
        query_parameters={'template': {'selective': selective}}
      )
    result = executor.execute(title='test', query=query, context=context)
    assert result == expected_result

  def test_execute_allow_unsafe_macro(self, executor, engine):
    query = """
    --garf:allow-unsafe-macro
    CREATE TABLE test AS SELECT '{value}' AS one;
    """
    executor.execute(title='test', query=query)

    with engine.connect() as connection:
      result = connection.execute(sqlalchemy.text('select one from test'))
      for row in result:
        assert row.one == '{value}'

  def test_execute_disable_unsafe_macro(self, executor):
    query = """
    --garf:disable-unsafe-macro
    CREATE TABLE test AS SELECT '{value}' AS one;
    """
    with pytest.raises(
      query_editor.GarfMacroError, match="No value provided for macro 'value'"
    ):
      executor.execute(title='test', query=query)

  def test_execute_replaces_macro(self, executor, engine):
    query = """
    CREATE TABLE test AS SELECT '{value}' AS one;
    """
    executor.execute(
      title='test',
      query=query,
      context=execution_context.ExecutionContext(
        query_parameters={'macro': {'value': '1'}}
      ),
    )

    with engine.connect() as connection:
      result = connection.execute(sqlalchemy.text('select one from test'))
      for row in result:
        assert row.one == '1'
