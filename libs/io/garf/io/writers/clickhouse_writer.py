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
"""Module for writing data to ClickHouse."""

from __future__ import annotations

import os

try:
  import clickhouse_connect
except ImportError as e:
  raise ImportError(
    'Please install garf-io with ClickHouse support - '
    '`pip install garf-io[clickhouse]`'
  ) from e

import logging
from typing import Any, Literal

import pandas as pd
from garf.core import report as garf_report
from garf.io import exceptions, formatter
from garf.io.telemetry import tracer
from garf.io.writers import abs_writer

logger = logging.getLogger(__name__)


class ClickHouseWriterError(exceptions.GarfIoError):
  """ClickHouseWriter specific errors."""


_CLICKHOUSE_TYPE_MAP = {
  'int64': 'Int64',
  'int32': 'Int32',
  'float64': 'Float64',
  'bool': 'Bool',
  'datetime64[ns]': 'DateTime64',
  'object': 'String',
}


def _pandas_dtype_to_clickhouse(dtype: str) -> str:
  return _CLICKHOUSE_TYPE_MAP.get(str(dtype), 'String')


class ClickHouseWriter(abs_writer.AbsWriter):
  """Handles writing GarfReports data to ClickHouse.

  Attributes:
    host: ClickHouse host.
    port: ClickHouse HTTP port.
    database: Database to use.
    secure: Whether to use HTTPS.
    if_exists: Behaviour when data already exists in the table.
    client: clickhouse-connect client instance.
  """

  def __init__(
    self,
    host: str = os.getenv('CLICKHOUSE_HOST', 'localhost'),
    port: int = os.getenv('_CLICKHOUSE_PORT', '8123'),
    database: str = 'default',
    username: str = os.getenv('CLICKHOUSE_USER', 'default'),
    password: str = os.getenv('CLICKHOUSE_PASSWORD', ''),
    secure: bool = False,
    if_exists: Literal['replace', 'append'] = 'replace',
    client: Any | None = None,
    **kwargs: Any,
  ) -> None:
    """Initializes ClickHouseWriter.

    Args:
      host: ClickHouse host.
      port: ClickHouse HTTP port.
      database: Database to use.
      username: Username for authentication.
      password: Password for authentication.
      secure: Whether to use HTTPS.
      if_exists: Behaviour when data already exists in the table:
        'replace' drops and recreates the table,
        'append' inserts into existing table,
        'create' creates table if it does not exist then inserts.
      client: Pre-configured clickhouse-connect client.
      kwargs: Additional arguments passed to clickhouse_connect.get_client.
    """
    super().__init__(**kwargs)
    self.host = host
    self.port = int(port)
    self.database = database
    self.secure = secure
    self.if_exists = if_exists
    if client is not None:
      self.client = client
    else:
      self.client = clickhouse_connect.get_client(
        host=host,
        port=port,
        database=database,
        username=username,
        password=password,
        secure=secure,
        **kwargs,
      )

  @tracer.start_as_current_span('clickhouse.write')
  def write(self, report: garf_report.GarfReport, destination: str) -> None:
    """Writes Garf report to the table.

    Args:
      report: GarfReport to be written.
      destination: Name of the output table, optionally `db.table`.

    Raises:
      ClickHouseWriterError: If unsupported overwrite strategy is provided.
    """
    report = self.format_for_write(report)
    destination = formatter.format_extension(
      destination,
      prefix=self.options.prefix,
      suffix=self.options.suffix,
    )
    database, table = self._split_destination(destination)
    if not report:
      df = pd.DataFrame(
        data=report.results_placeholder, columns=report.column_names
      ).head(0)
    else:
      df = report.to_pandas()
    logger.debug('Writing %d rows of data to %s.%s', len(df), database, table)
    self.client.command(f'CREATE DATABASE IF NOT EXISTS `{database}`')
    self._create_table(database, table, df, if_not_exists=True)
    if self.if_exists == 'replace':
      self.client.command(f'DROP TABLE IF EXISTS `{database}`.`{table}`')
      self._create_table(database, table, df)
    elif self.if_exists == 'append':
      pass
    else:
      raise ClickHouseWriterError(
        f'Unsupported overwrite strategy: {self.if_exists}'
      )
    self.client.insert(
      table,
      df.values.tolist(),
      column_names=list(df.columns),
      database=database,
    )
    logger.debug('Writing to %s.%s is completed', database, table)

  def _split_destination(self, destination: str) -> tuple[str, str]:
    parts = destination.split('.')
    if len(parts) == 2:
      return parts[0], parts[1]
    return self.database, destination

  def _create_table(
    self,
    database: str,
    table: str,
    df: pd.DataFrame,
    if_not_exists: bool = False,
  ) -> None:
    columns = ', '.join(
      f'`{col}` {_pandas_dtype_to_clickhouse(str(dtype))}'
      for col, dtype in zip(df.columns, df.dtypes)
    )
    guard = 'IF NOT EXISTS ' if if_not_exists else ''
    self.client.command(
      f'CREATE TABLE {guard}`{database}`.`{table}` ({columns}) '
      'ENGINE = MergeTree() ORDER BY tuple()'
    )
