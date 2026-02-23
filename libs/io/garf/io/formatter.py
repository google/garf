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
"""Module for formatting Garf reports before writing."""

from __future__ import annotations

import datetime
from enum import Enum
from pathlib import Path
from typing import Literal, Union, get_args

from garf.core import api_clients
from garf.core import report as garf_report
from garf.io.telemetry import tracer
from typing_extensions import TypeAlias

_NESTED_FIELD: TypeAlias = Union[list, tuple]


class FormattingStrategy:
  """Interface for all formatting strategies applied to GarfReport."""

  def __init__(self, columns: str | None = None) -> str:
    self.columns = columns.split(',') if columns else []

  def _cast_to_enum(self, enum: type[Enum], value: str | Enum) -> Enum:
    """Ensures that strings are always converted to Enums."""
    return enum[value.upper()] if isinstance(value, str) else value

  @tracer.start_as_current_span('apply_transformations')
  def apply_transformations(
    self, report: garf_report.GarfReport
  ) -> garf_report.GarfReport:
    """Replaces arrays in the report."""
    formatted_rows = self._format_rows(report.results)
    formatted_placeholders = self._format_rows(report.results_placeholder)
    return garf_report.GarfReport(
      results=formatted_rows,
      column_names=report.column_names,
      results_placeholder=formatted_placeholders,
    )

  def _format_rows(
    self, rows: list[list[api_clients.ApiRowElement]]
  ) -> list[list[api_clients.ApiRowElement]]:
    """Formats rows of report based on formatting strategy for each element.

    Args:
      rows: Rows in report.

    Returns:
      Formatted rows.
    """
    formatted_rows = []
    for row in rows:
      formatted_row = []
      for field in row:
        formatted_row.append(self.format_field(field))
      formatted_rows.append(formatted_row)
    return formatted_rows

  def format_field(
    self, field: api_clients.ApiRowElement
  ) -> api_clients.ApiRowElement:
    raise NotImplementedError


class DateHandlingStrategy(FormattingStrategy):
  def __init__(
    self,
    type: Literal['strings', 'dates', 'datetimes', 'timestamp'] = 'strings',
    format_string: str | None = None,
  ) -> None:
    self.type_ = type
    self.format_string = format_string or '%Y-%m-%d'

  def format_field(self, field) -> datetime.date:
    try:
      datetime_obj = datetime.datetime.strptime(field, self.format_string)
      if self.type_ == 'dates':
        return datetime_obj.date()
      if self.type_ == 'datetimes':
        return datetime_obj
      if self.type_ == 'timestamps':
        return datetime_obj.timestamp()

    except TypeError:
      return field

  def apply_transformations(
    self, report: garf_report.GarfReport
  ) -> garf_report.GarfReport:
    """Replaces arrays in the report."""
    if self.type_ == 'strings':
      return report
    return super().apply_transformations(report)


class DateTimeHandlingStrategy(FormattingStrategy):
  def __init__(
    self,
    type: Literal['strings', 'datetimes'] = 'strings',
    format_string: str | None = None,
  ) -> None:
    self.type_ = type
    self.format_string = format_string or '%Y-%m-%d %H:%M-%S'

  def format_field(self, field) -> datetime.date:
    try:
      return datetime.datetime.strptime(field, self.format_string)
    except TypeError:
      return field

  def apply_transformations(
    self, report: garf_report.GarfReport
  ) -> garf_report.GarfReport:
    """Replaces arrays in the report."""
    if self.type_ == 'strings':
      return report
    return super().apply_transformations(report)


class ArrayHandling(Enum):
  """Specifies acceptable options for ArrayHandlingStrategy."""

  STRINGS = 1
  ARRAYS = 2


class ArrayHandlingStrategy(FormattingStrategy):
  """Handles arrays in the report.

  Arrays can be left as-is or converted to strings with required delimiter.

  Attributes:
    type_: Type of array handling (ARRAYS, STRINGS).
    delimiter: Symbol used as delimiter when type_ is STRINGS.
  """

  def __init__(
    self,
    type_: ArrayHandling | str = ArrayHandling.STRINGS,
    delimiter: str = '|',
  ) -> None:
    """Initializes strategy based on type_ and delimiter.

    Args:
        type_: Type of array handling (ARRAYS, STRINGS).
        delimiter: Symbol used as delimiter when type_ is STRINGS.
    """
    self.type_ = self._cast_to_enum(ArrayHandling, type_)
    self.delimiter = delimiter

  def format_field(self, field):
    if isinstance(field, get_args(_NESTED_FIELD)):
      return self.delimiter.join([str(element) for element in field])
    return field

  def apply_transformations(
    self, report: garf_report.GarfReport
  ) -> garf_report.GarfReport:
    """Replaces arrays in the report."""
    if self.type_ == ArrayHandling.ARRAYS:
      return report
    return super().apply_transformations(report)


@tracer.start_as_current_span('format_report_for_writing')
def format_report_for_writing(
  report: garf_report.GarfReport,
  formatting_strategies: list[FormattingStrategy],
) -> garf_report.GarfReport:
  """Applies formatting strategies to report.

  Args:
      report: Report that needs to be formatted.
      formatting_strategies: Strategies to be applied to report.

  Returns:
      New report with updated data.
  """
  for strategy in formatting_strategies:
    report = strategy.apply_transformations(report)
  report.disable_scalar_conversions()
  return report


def format_extension(
  path_object: str, current_extension: str = '.sql', new_extension: str = ''
) -> str:
  """Formats query path to required extension.

  Args:
      path_object: Path to query.
      current_extension: Extension of the query.
      new_extension: Required extension

  Returns:
     Path with an updated extension.
  """
  path_object_name = Path(path_object).name
  if len(path_object_name.split('.')) > 1:
    return path_object_name.replace(current_extension, new_extension)
  return f'{path_object}{new_extension}'
