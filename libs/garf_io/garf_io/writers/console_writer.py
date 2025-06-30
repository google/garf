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
"""Module for writing data with console."""

from __future__ import annotations

from typing import Literal

import rich
from rich import console, table

from garf_core import report as garf_report
from garf_io.writers import abs_writer


class ConsoleWriter(abs_writer.AbsWriter):
  """Writes reports to standard output.

  Attributes:
    page_size: How many row of report should be written
    type: Type of output ('table', 'json').
  """

  def __init__(
    self,
    page_size: int = 10,
    format: Literal['table', 'json', 'jsonl'] = 'table',
    **kwargs: str,
  ) -> None:
    """Initializes ConsoleWriter.

    Args:
        page_size: How many row of report should be written
        format: Type of output.
        kwargs: Optional parameter to initialize writer.
    """
    super().__init__(**kwargs)
    self.page_size = int(page_size)
    self.format = format

  def write(self, report: garf_report.GarfReport, destination: str) -> None:
    """Writes Garf report to standard output.

    Args:
      report: Garf report.
      destination: Base file name report should be written to.
    """
    report = self.format_for_write(report)
    if self.format == 'table':
      self._write_rich_table(report, destination)
    elif self.format == 'json':
      print(report.to_json())
    elif self.format == 'jsonl':
      print(report.to_jsonl())

  def _write_rich_table(
    self, report: garf_report.GarfReport, destination: str
  ) -> None:
    output_table = table.Table(
      title=f'showing results for query <{destination.split("/")[-1]}>',
      caption=(
        f'showing rows 1-{min(self.page_size, len(report))} '
        f'out of total {len(report)}'
      ),
      box=rich.box.MARKDOWN,
    )
    for header in report.column_names:
      output_table.add_column(header)
    for i, row in enumerate(report):
      if i < self.page_size:
        output_table.add_row(*[str(field) for field in row])
    console.Console().print(output_table)
