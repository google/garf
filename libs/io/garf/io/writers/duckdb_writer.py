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
"""Module for writing data to DuckDB."""

from __future__ import annotations

try:
  import duckdb
except ImportError as e:
  raise ImportError(
    'Please install garf-io with DuckDB support - `pip install garf-io[duckdb]`'
  ) from e

import logging
from typing import Literal

import pandas as pd
from garf.core import report as garf_report
from garf.io import exceptions, formatter
from garf.io.telemetry import tracer
from garf.io.writers import abs_writer

logger = logging.getLogger(__name__)


class DuckDBWriterError(exceptions.GarfIoError):
  """DuckDBWriterError specific errors."""


class DuckDBWriter(abs_writer.AbsWriter):
  """Handles writing GarfReports data to DuckDB.

  Attributes:
    db: Database location.
  """

  def __init__(
    self,
    db: str,
    if_exists: str = Literal['replace', 'append', 'create'],
    **kwargs,
  ):
    """Initializes DuckDBWriter based on db file.

    Args:
      db: Database location.
    if_exists: Behaviour when data already exists in the table.
    """
    super().__init__(**kwargs)
    self.db = db
    self.if_exists = if_exists
    self.api_client = duckdb.connect(database=db)

  @tracer.start_as_current_span('duckdb.write')
  def write(self, report: garf_report.GarfReport, destination: str) -> None:
    """Writes Garf report to the table.

    Args:
      report: GarfReport to be written.
      destination: Name of the output table.
    """
    report = self.format_for_write(report)
    destination = formatter.format_extension(
      destination,
      prefix=self.options.prefix,
      suffix=self.options.suffix,
    )
    if not report:
      df = pd.DataFrame(
        data=report.results_placeholder, columns=report.column_names
      ).head(0)
    else:
      df = report.to_pandas()
    logger.debug('Writing %d rows of data to %s', len(df), destination)
    if self.if_exists == 'replace':
      self.api_client.execute(
        f'CREATE OR REPLACE TABLE {destination} AS SELECT * FROM df'
      )
    elif self.if_exists == 'append':
      self.api_client.execute(
        f'INSERT INTO {destination} BY NAME (SELECT * FROM df) '
      )
    elif self.if_exists == 'create':
      self.api_client.execute(
        f'CREATE TABLE IF NOT EXISTS {destination} AS SELECT * FROM df'
      )
    else:
      raise DuckDBExecutorError(
        f'Unsupported overwrite strategy: {self.if_exists}'
      )
    logger.debug('Writing to %s is completed', destination)
