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
"""Writes GarfReport to Excel.

Writing to remote storage systems (gs, s3, hadoop, stfp) is also supported.
"""

from __future__ import annotations

import logging
import os
import pathlib
from typing import Optional, Union

import smart_open
from garf.core import report as garf_report
from garf.io import formatter
from garf.io.telemetry import tracer
from garf.io.writers import file_writer

try:
  import pandas as pd
except ImportError as e:
  raise ImportError(
    'Please install garf-io with Excel support - `pip install garf-io[excel]`'
  ) from e

logger = logging.getLogger(__name__)


class ExcelWriter(file_writer.FileWriter):
  """Writes Garf Report to Excel files.

  Attributes:
    destination_folder: Destination where Excel files are stored.
    file: Optional file to write report(s) to.
  """

  def __init__(
    self,
    destination_folder: Union[
      str, os.PathLike[str], pathlib.Path
    ] = pathlib.Path.cwd(),
    file: Optional[Union[str, os.PathLike[str], pathlib.Path]] = None,
    **kwargs,
  ) -> None:
    """Initializes ExcelWriter based on a destination_folder and file name.

    Args:
      destination_folder: Destination where Excel files are stored.
      file: Optional file to write report(s) to.
      kwargs: Optional keyword arguments to initialize writer.
    """
    self.file = file
    super().__init__(destination_folder=destination_folder, **kwargs)

  def __str__(self):
    return f'[Excel] - data are saved to {self.destination_folder} destination_folder.'

  @tracer.start_as_current_span('excel.write')
  def write(self, report: garf_report.GarfReport, destination: str) -> str:
    """Writes Garf report to a Excel sheet.

    Args:
      report: Garf report.
      destination: Sheet name report should be written to.

    Returns:
      Full path where data are written.
    """
    report = self.format_for_write(report)

    if not self.file:
      destination = formatter.format_extension(
        destination, new_extension='.xlsx'
      )
      output_path = os.path.join(self.destination_folder, destination)
      sheet_name = 'garf'
    else:
      output_path = os.path.join(self.destination_folder, self.file)
      sheet_name = destination
    self.create_dir()
    logger.debug(
      'Writing %d rows of data to file %s, sheet %s',
      len(report),
      output_path,
      destination,
    )
    with (
      smart_open.open(
        output_path,
        mode='wb',
      ) as f,
      pd.ExcelWriter(f, engine='openpyxl') as writer,
    ):
      report.to_pandas().to_excel(writer, sheet_name=sheet_name, index=False)
    logger.debug('Writing to %s is completed', output_path)
    return f'[Excel] - at {output_path}'
