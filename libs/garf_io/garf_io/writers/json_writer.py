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
"""Module for writing data to JSON."""

from __future__ import annotations

import logging
import os
from typing import Literal

import smart_open

from garf_core import report as garf_report
from garf_io import formatter
from garf_io.writers import file_writer


class JsonWriter(file_writer.FileWriter):
  """Writes Garf Report to JSON.

  Attributes:
      destination_folder: Destination where JSON files are stored.
  """

  def __init__(
    self,
    destination_folder: str | os.PathLike = os.getcwd(),
    format: Literal['json', 'jsonl'] = 'json',
    **kwargs: str,
  ) -> None:
    """Initializes JsonWriter based on a destination_folder.

    Args:
      destination_folder: A local folder where JSON files are stored.
      format: Format of json file ('json', 'jsonl').
      kwargs: Optional keyword arguments to initialize writer.
    """
    super().__init__(destination_folder=destination_folder, **kwargs)
    self.format = format

  def write(self, report: garf_report.GarfReport, destination: str) -> str:
    """Writes Garf report to a JSON file.

    Args:
      report: Garf report.
      destination: Base file name report should be written to.

    Returns:
      Base filename where data are written.
    """
    report = self.format_for_write(report)
    file_extension = '.json' if self.format == 'json' else '.jsonl'
    destination = formatter.format_extension(
      destination, new_extension=file_extension
    )
    self.create_dir()
    logging.debug('Writing %d rows of data to %s', len(report), destination)
    output_path = os.path.join(self.destination_folder, destination)
    with smart_open.open(output_path, 'w', encoding='utf-8') as f:
      f.write(report.to_json(output=self.format))
    logging.debug('Writing to %s is completed', output_path)
    return f'[JSON] - at {output_path}'
