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
"""Module for writing data to Neo4j database."""

from __future__ import annotations

import logging
import os
from typing import Any, Literal

try:
  import neo4j
except ImportError as e:
  raise ImportError(
    'Please install garf-io with Neo4j support - `pip install garf-io[neo4j]`'
  ) from e

from garf.core import report as garf_report
from garf.io import exceptions, formatter
from garf.io.telemetry import tracer
from garf.io.writers import abs_writer

logger = logging.getLogger(__name__)


class Neo4jWriterError(exceptions.GarfIoError):
  """Neo4jWriter specific errors."""


class Neo4jWriterOptions(abs_writer.WriterOptions):
  """Options for writing report to Neo4j.

  Attributes:
    uri: Neo4j database URI (e.g., bolt://localhost:7687).
    username: Username for authentication.
    password: Password for authentication.
    database: Neo4j database to write to.
    label_prefix: Prefix for node labels (default: None).
    relationship_type: Type for relationships between nodes (default: None).
    if_exists: Behavior when data already exists:
      'merge' - merge nodes with same properties,
      'create' - create new nodes always,
      'delete' - delete existing nodes before inserting.
    relationship_properties: Optional additional properties for relationships.
  """

  model_config = abs_writer.WriterOptions.model_config

  uri: str = os.getenv('NEO4J_URI', 'bolt://localhost:7687')
  username: str = os.getenv('NEO4J_USERNAME', 'neo4j')
  password: str = os.getenv('NEO4J_PASSWORD', '')
  database: str = 'neo4j'
  label_prefix: str | None = None
  relationship_type: str | None = None
  if_exists: Literal['merge', 'create', 'delete'] = 'merge'
  relationship_properties: dict[str, Any] | None = None

  def model_post_init(self, __context) -> None:
    """Validate and configure options after initialization."""
    if not self.uri.startswith(('bolt://', 'neo4j://')):
      raise Neo4jWriterError(
        f'Invalid URI scheme. Expected bolt:// or neo4j://, got: {self.uri}'
      )

    valid_options = ['merge', 'create', 'delete']
    if self.if_exists not in valid_options:
      valid_options = ', '.join(valid_options)
      raise Neo4jWriterError(
        f'Unsupported if_exists value: {self.if_exists}. '
        f'Choose one of: {valid_options}'
      )


class Neo4jWriter(abs_writer.AbsWriter):
  """Writes Garf Report to Neo4j graph database.

  This writer creates nodes and relationships in a Neo4j graph database based
  on the report data. Each row in the report becomes a node, and relationships
  are created between consecutive nodes.

  Attributes:
    driver: Neo4j driver instance.
    options: Writer options configuration.
  """

  def __init__(
    self,
    options: Neo4jWriterOptions | None = None,
    **kwargs: Any,
  ) -> None:
    """Initializes Neo4jWriter.

    Args:
      options: Optional Neo4jWriterOptions configuration.
      kwargs: Additional keyword arguments passed to options.
    """
    super().__init__(**kwargs)
    self.options = options if options else Neo4jWriterOptions(**kwargs)

    self._driver = None
    self._driver_initialized = False

  def __str__(self) -> str:
    """String representation of the writer."""
    return f'[Neo4j] - {self.options.database} at {self.options.uri}'

  @property
  def driver(self) -> neo4j.GraphDatabase.driver:
    """Lazy initialization of Neo4j driver."""
    if not self._driver_initialized:
      with tracer.start_as_current_span('neo4j.create_driver'):
        self._driver = neo4j.GraphDatabase.driver(
          uri=self.options.uri,
          auth=(self.options.username, self.options.password),
          database=self.options.database,
        )
        self._driver_initialized = True
    return self._driver

  @driver.setter
  def driver(self, value: neo4j.GraphDatabase.driver):
    """Setter for driver property."""
    self._driver = value
    self._driver_initialized = True

  @tracer.start_as_current_span('neo4j.write')
  def write(self, report: garf_report.GarfReport, destination: str) -> str:
    """Writes Garf report to Neo4j database.

    Creates nodes from each row of the report and relationships between them.
    Node labels are constructed from column names with optional prefix.

    Args:
      report: GarfReport to be written.
      destination: Name of the graph pattern/relationship type to use.

    Returns:
      String indicating successful write operation.

    Raises:
      Neo4jWriterError: If write operation fails or configuration is invalid.
    """
    if not report:
      logger.warning('Empty report, nothing to write')
      return f'[Neo4j] - empty report at {destination}'
    driver = self.driver
    destination = formatter.format_extension(
      destination,
      prefix=self.options.prefix,
      suffix=self.options.suffix,
    )

    report = self.format_for_write(report)
    data = report.to_list(row_type='dict')

    label_columns = [col for col in report.column_names if col != destination]
    node_label = f'Node:{self.options.label_prefix or destination}'
    if label_columns:
      node_label += ':' + ','.join(label_columns)

    rel_type = (
      f'RELATIONSHIP:{self.options.relationship_type or destination}'
      if self.options.relationship_type
      else f'RELATIONSHIP:{destination}'
    )

    with driver.session() as session:
      if self.options.if_exists == 'merge':
        result = self._execute_merge(session, node_label, rel_type, data)
      elif self.options.if_exists == 'create':
        result = self._execute_create(session, node_label, rel_type, data)
      else:
        result = self._execute_delete(session, node_label, rel_type)

      logger.debug('Writing %d rows of data to Neo4j', len(data))

      if result:
        summary = result.summary
        logger.info(
          'Successfully wrote %d rows to Neo4j. '
          'Created: %d, Matched: %d, Updated: %d',
          len(data),
          summary.counters.create,
          summary.counters.match,
          summary.counters.update,
        )

    return f'[Neo4j] - at {destination} in database {self.options.database}'

  def _execute_merge(
    self,
    session: neo4j.Session,
    node_label: str,
    rel_type: str,
    data: list[dict],
  ) -> neo4j.Result:
    """Builds and runs a MERGE query for upserting nodes and relationships."""
    columns = list(data[0].keys())

    node_conditions = ' AND '.join(
      f'{col} = {columns.index(col)}' for col in columns
    )
    node_merge = f"""
    MERGE (n:{node_label} {{{node_conditions}}})
    SET n:destination
    """

    rel_merge = f"""
    WITH n
    FOREACH (row IN range(0, size(data)-2))
    WITH prev_row = data[row], curr_row = data[row+1]
    MATCH (p:Node) WHERE p.destination = prev_row.destination
    OR p.label = prev_row.label
    MATCH (c:Node) WHERE c.destination = curr_row.destination
    OR c.label = curr_row.label
    CREATE (p)-[:{rel_type}]->(c)
    """

    return session.run(node_merge + rel_type + rel_merge)

  def _execute_create(
    self,
    session: neo4j.Session,
    node_label: str,
    rel_type: str,
    data: list[dict],
  ) -> neo4j.Result:
    """Builds and executes a Cypher CREATE query for creating nodes."""
    columns = list(data[0].keys())

    set_clauses = []
    for col in columns:
      set_clauses.append(f'n.{col} = {columns.index(col)}')
    node_create = f"""
    CREATE (n:{node_label})
    SET {' , '.join(set_clauses)}
    """

    rel_create = f"""
    WITH n
    FOREACH (row IN range(0, size(data)-2))
    MATCH (p) WHERE p.destination = data[row].destination
    OR p.label = data[row].label
    MATCH (c) WHERE c.destination = data[row+1].destination
    OR c.label = data[row+1].label
    CREATE (p)-[:{rel_type}]->(c)
    """

    return session.run(node_create + rel_create)

  def _execute_delete(
    self,
    session: neo4j.Session,
    node_label: str,
    rel_type: str,
  ) -> neo4j.Result:
    """Builds and executes a Cypher DELETE query for removing existing data."""
    return session.run(f"""
    MATCH (n:{node_label})
    DETACH DELETE n
    MATCH (p)-[:{rel_type}]->(c)
    DELETE (p), (c)
    """)

  def close(self):
    """Closes the Neo4j driver connection."""
    if self._driver:
      self._driver.close()
      logger.debug('Neo4j driver closed')
