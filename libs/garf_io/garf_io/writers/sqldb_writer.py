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
"""Module for writing data with SqlAlchemy."""

from __future__ import annotations

try:
  import sqlalchemy
except ImportError as e:
  raise ImportError(
    'Please install garf-io with sqlalchemy support '
    '- `pip install garf-io[sqlalchemy]`'
  ) from e

import logging

import pandas as pd

from garf_core import report as garf_report
from garf_io import formatter
from garf_io.writers import abs_writer


class SqlAlchemyWriter(abs_writer.AbsWriter):
  """Handles writing GarfReports data to databases supported by SqlAlchemy.

  Attributes:
      connection_string:
          Connection string to database.
          More at https://docs.sqlalchemy.org/en/20/core/engines.html.
      if_exists:
          Behaviour when data already exists in the table.
  """

  def __init__(
    self, connection_string: str, if_exists: str = 'replace', **kwargs
  ):
    """Initializes SqlAlchemyWriter based on connection_string.

    Args:
        connection_string: Connection string to database.
    if_exists: Behaviour when data already exists in the table.
    """
    super().__init__(**kwargs)
    self.connection_string = connection_string
    self.if_exists = if_exists

  def write(self, report: garf_report.GarfReport, destination: str) -> None:
    """Writes Garf report to the table.

    Args:
        report: GarfReport to be written.
        destination: Name of the output table.
    """
    report = self.format_for_write(report)
    destination = formatter.format_extension(destination)
    dtypes = {}
    for column in report.column_names:
      if (report and isinstance(report[0][column], dict)) or (
        not report and isinstance(report.results_placeholder[0][column], dict)
      ):
        dtypes.update({column: sqlalchemy.types.JSON})
    if not report:
      df = pd.DataFrame(
        data=report.results_placeholder, columns=report.column_names
      ).head(0)
    else:
      df = report.to_pandas()
    logging.debug('Writing %d rows of data to %s', len(df), destination)
    write_params = {
      'name': destination,
      'con': self.engine,
      'index': False,
      'if_exists': self.if_exists,
    }
    if dtypes:
      write_params.update({'dtype': dtypes})
    df.to_sql(**write_params)
    logging.debug('Writing to %s is completed', destination)

  @property
  def engine(self) -> sqlalchemy.engine.Engine:
    """Creates engine based on connection string."""
    return sqlalchemy.create_engine(self.connection_string)
