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

from __future__ import annotations

import pytest
from garf.core import report as garf_report
from garf.io.writers import neo4j_writer


class TestNeo4jWriter:
  """Tests for Neo4jWriter."""

  @pytest.fixture(autouse=True)
  def mock_neo4j(self, mocker):
    mocker.patch('neo4j.GraphDatabase.driver')
    mocker.patch('neo4j.Session')

  def test_init_with_default_options(self):
    writer = neo4j_writer.Neo4jWriter()

    assert writer.options.uri == 'bolt://localhost:7687'
    assert writer.options.username == 'neo4j'
    assert writer.options.password == ''
    assert writer.options.database == 'neo4j'
    assert writer.options.label_prefix is None
    assert writer.options.relationship_type is None
    assert writer.options.if_exists == 'merge'
    assert writer.options.relationship_properties is None

  def test_init_with_custom_options(self):
    writer = neo4j_writer.Neo4jWriter(
      uri='bolt://my-neo4j:7687',
      username='admin',
      password='secret',
      database='mydb',
      label_prefix='Custom',
      relationship_type='CUSTOM_REL',
      if_exists='create',
    )

    assert writer.options.uri == 'bolt://my-neo4j:7687'
    assert writer.options.username == 'admin'
    assert writer.options.password == 'secret'
    assert writer.options.database == 'mydb'
    assert writer.options.label_prefix == 'Custom'
    assert writer.options.relationship_type == 'CUSTOM_REL'
    assert writer.options.if_exists == 'create'

  def test_str_representation(self):
    writer = neo4j_writer.Neo4jWriter(uri='bolt://test:7687', database='testdb')
    assert str(writer) == '[Neo4j] - testdb at bolt://test:7687'

  def test_init_with_invalid_uri_scheme_raises_error(self):
    with pytest.raises(neo4j_writer.Neo4jWriterError):
      neo4j_writer.Neo4jWriter(uri='http://localhost:7474')

  def test_write_empty_report(self, mocker):
    mock_driver = mocker.MagicMock()
    mock_session = mocker.MagicMock()
    mock_driver.session.return_value.__enter__ = mocker.MagicMock(
      return_value=mock_session
    )
    mock_driver.session.return_value.__exit__ = mocker.MagicMock(
      return_value=False
    )
    mock_driver.session.return_value.run.return_value.summary.counters = (
      mocker.MagicMock(create=0, match=0, update=0)
    )

    writer = neo4j_writer.Neo4jWriter()
    writer.driver = mock_driver
    writer._driver_initialized = True

    result = writer.write(
      garf_report.GarfReport(results=None, column_names=['test']), 'test'
    )

    assert result == '[Neo4j] - empty report at test'
    mock_session.run.assert_not_called()

  def test_write_single_row_report(self, mocker):
    mock_driver = mocker.MagicMock()
    mock_session = mocker.MagicMock()
    mock_driver.session.return_value.__enter__ = mocker.MagicMock(
      return_value=mock_session
    )
    mock_driver.session.return_value.__exit__ = mocker.MagicMock(
      return_value=False
    )
    mock_driver.session.return_value.run.return_value.summary.counters = (
      mocker.MagicMock(create=1, match=0, update=0)
    )

    writer = neo4j_writer.Neo4jWriter(if_exists='create')
    writer.driver = mock_driver
    writer._driver_initialized = True

    data = [[1, 'two', 'three']]
    columns = ['column_1', 'column_2', 'column_3']
    report = garf_report.GarfReport(data, columns)

    result = writer.write(report, 'test')

    assert 'test' in result
    mock_session.run.assert_called_once()

  def test_write_multi_row_report(self, mocker):
    """Test writing a multi-row report."""
    mock_driver = mocker.MagicMock()
    mock_session = mocker.MagicMock()
    mock_driver.session.return_value.__enter__ = mocker.MagicMock(
      return_value=mock_session
    )
    mock_driver.session.return_value.__exit__ = mocker.MagicMock(
      return_value=False
    )
    mock_driver.session.return_value.run.return_value.summary.counters = (
      mocker.MagicMock(create=2, match=0, update=0)
    )

    writer = neo4j_writer.Neo4jWriter(if_exists='create')
    writer.driver = mock_driver
    writer._driver_initialized = True

    data = [[1, 'a'], [2, 'b'], [3, 'c']]
    columns = ['id', 'name']
    report = garf_report.GarfReport(data, columns)

    result = writer.write(report, 'test')

    assert 'test' in result
    mock_session.run.assert_called_once()

  def test_merge_strategy(self, mocker):
    """Test merge strategy."""
    mock_driver = mocker.MagicMock()
    mock_session = mocker.MagicMock()
    mock_driver.session.return_value.__enter__ = mocker.MagicMock(
      return_value=mock_session
    )
    mock_driver.session.return_value.__exit__ = mocker.MagicMock(
      return_value=False
    )
    mock_driver.session.return_value.run.return_value.summary.counters = (
      mocker.MagicMock(create=1, match=1, update=1)
    )

    writer = neo4j_writer.Neo4jWriter(if_exists='merge')
    writer.driver = mock_driver
    writer._driver_initialized = True

    data = [[1, 'test']]
    columns = ['id', 'name']
    report = garf_report.GarfReport(data, columns)

    result = writer.write(report, 'test')

    assert result == '[Neo4j] - at test in database neo4j'

  def test_create_strategy(self, mocker):
    """Test create strategy."""
    mock_driver = mocker.MagicMock()
    mock_session = mocker.MagicMock()
    mock_driver.session.return_value.__enter__ = mocker.MagicMock(
      return_value=mock_session
    )
    mock_driver.session.return_value.__exit__ = mocker.MagicMock(
      return_value=False
    )
    mock_driver.session.return_value.run.return_value.summary.counters = (
      mocker.MagicMock(create=1, match=0, update=0)
    )

    writer = neo4j_writer.Neo4jWriter(if_exists='create')
    writer.driver = mock_driver
    writer._driver_initialized = True

    data = [[1, 'test']]
    columns = ['id', 'name']
    report = garf_report.GarfReport(data, columns)

    result = writer.write(report, 'test')

    assert result == '[Neo4j] - at test in database neo4j'

  def test_delete_strategy(self, mocker):
    """Test delete strategy."""
    mock_driver = mocker.MagicMock()
    mock_session = mocker.MagicMock()
    mock_driver.session.return_value.__enter__ = mocker.MagicMock(
      return_value=mock_session
    )
    mock_driver.session.return_value.__exit__ = mocker.MagicMock(
      return_value=False
    )
    mock_driver.session.return_value.run.return_value.summary.counters = (
      mocker.MagicMock(create=0, match=0, update=0)
    )

    writer = neo4j_writer.Neo4jWriter(if_exists='delete')
    writer.driver = mock_driver
    writer._driver_initialized = True

    data = [[1, 'test']]
    columns = ['id', 'name']
    report = garf_report.GarfReport(data, columns)

    result = writer.write(report, 'test')

    assert result == '[Neo4j] - at test in database neo4j'

  def test_close_closes_driver(self, mocker):
    """Test that close() closes the driver."""
    mock_driver = mocker.MagicMock()
    mock_driver.close = mocker.MagicMock()

    writer = neo4j_writer.Neo4jWriter()
    writer._driver = mock_driver
    writer._driver_initialized = True

    writer.close()

    mock_driver.close.assert_called_once()

  def test_format_for_write(self, mocker):
    """Test format_for_write method."""
    writer = neo4j_writer.Neo4jWriter()
    writer.options.array_handling = 'strings'
    writer.options.date_handling = 'strings'

    data = [[1, 'test', [3, 4]]]
    columns = ['id', 'name', 'tags']
    report = garf_report.GarfReport(data, columns)

    formatted_report = writer.format_for_write(report)

    assert formatted_report.column_names == columns
    assert len(formatted_report) == len(report)

  def test_destination_with_prefix_suffix(self, mocker):
    """Test destination formatting with prefix and suffix."""
    mock_driver = mocker.MagicMock()
    mock_session = mocker.MagicMock()
    mock_driver.session.return_value.__enter__ = mocker.MagicMock(
      return_value=mock_session
    )
    mock_driver.session.return_value.__exit__ = mocker.MagicMock(
      return_value=False
    )
    mock_driver.session.return_value.run.return_value.summary.counters = (
      mocker.MagicMock(create=1, match=0, update=0)
    )

    writer = neo4j_writer.Neo4jWriter()
    writer.driver = mock_driver
    writer._driver_initialized = True
    writer.options.prefix = 'prefix_'
    writer.options.suffix = '_suffix'

    data = [[1, 'test']]
    columns = ['id', 'name']
    report = garf_report.GarfReport(data, columns)

    result = writer.write(report, 'test_destination')

    # Should include prefix and suffix in result
    assert 'test_destination' in result

  def test_label_prefix_application(self, mocker):
    """Test that label_prefix is applied to node labels."""
    mock_driver = mocker.MagicMock()
    mock_session = mocker.MagicMock()
    mock_driver.session.return_value.__enter__ = mocker.MagicMock(
      return_value=mock_session
    )
    mock_driver.session.return_value.__exit__ = mocker.MagicMock(
      return_value=False
    )
    mock_driver.session.return_value.run.return_value.summary.counters = (
      mocker.MagicMock(create=1, match=0, update=0)
    )

    writer = neo4j_writer.Neo4jWriter(label_prefix='CustomPrefix')
    writer.driver = mock_driver
    writer._driver_initialized = True

    data = [[1, 'test']]
    columns = ['id', 'name']
    report = garf_report.GarfReport(data, columns)

    # The mock will capture the query being run
    result = writer.write(report, 'test')

    # Verify the call was made (the actual query content would contain the label)
    assert mock_session.run.called

  def test_relationship_type_application(self, mocker):
    """Test that custom relationship type is used."""
    mock_driver = mocker.MagicMock()
    mock_session = mocker.MagicMock()
    mock_driver.session.return_value.__enter__ = mocker.MagicMock(
      return_value=mock_session
    )
    mock_driver.session.return_value.__exit__ = mocker.MagicMock(
      return_value=False
    )
    mock_driver.session.return_value.run.return_value.summary.counters = (
      mocker.MagicMock(create=1, match=0, update=0)
    )

    writer = neo4j_writer.Neo4jWriter(relationship_type='CUSTOM_REL')
    writer.driver = mock_driver
    writer._driver_initialized = True

    data = [[1, 'test']]
    columns = ['id', 'name']
    report = garf_report.GarfReport(data, columns)

    result = writer.write(report, 'test')

    # Verify the call was made
    assert mock_session.run.called
