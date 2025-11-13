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
"""Handles query parsing."""

from __future__ import annotations

import contextlib
import re
from typing import Literal, Union

import pydantic
from typing_extensions import TypeAlias

from garf_core import exceptions

QueryParameters: TypeAlias = dict[str, Union[str, float, int, list]]

CustomizerType: TypeAlias = Literal['resource_index', 'nested_field', 'slice']


class GarfQueryError(exceptions.GarfError):
  """Base exception for Garf queries."""


class GarfVirtualColumnError(GarfQueryError):
  """Specifies incorrect virtual column type."""


class GarfCustomizerError(GarfQueryError):
  """Specifies incorrect customizer."""


class GarfFieldError(GarfQueryError):
  """Specifies incorrect fields from API."""


class Customizer(pydantic.BaseModel):
  """Specifies extraction operation on a field.

  Attributes:
    type: Type of customizer.
    value: Value to be extracted from a field.
  """

  type: CustomizerType | None = None
  value: int | str | SliceField | None = None

  def __bool__(self) -> bool:
    """Evaluates whether all fields are not empty."""
    return bool(self.type and self.value)


class SliceField(pydantic.BaseModel):
  """Specifies slice with the content be extracted.

  Attributes:
    slice_literal: Slice to be extracted from a sequence.
    value: Value to be extracted from each element of a slice.
  """

  model_config = pydantic.ConfigDict(arbitrary_types_allowed=True)
  slice_literal: slice
  value: str | int


class ProcessedField(pydantic.BaseModel):
  """Stores field with its customizers.

  Attributes:
    field: Extractable field.
    customizer: Customizer to be applied to the field.
  """

  field: str
  customizer: Customizer = Customizer()

  @classmethod
  def from_raw(cls, raw_field: str) -> ProcessedField:
    """Process field to extract possible customizers.

    Args:
      raw_field: Unformatted field string value.

    Returns:
      ProcessedField that contains formatted field with customizers.
    """
    raw_field = raw_field.replace(r'\s+', '').strip()
    if _is_quoted_string(raw_field):
      return ProcessedField(field=raw_field)
    if len(slices := cls._extract_slices(raw_field)) > 1:
      field_name, op, slice_literal = slices
      start, *rest = op.split(':')
      if start == '':
        if not rest:
          slice_object = slice(None)
        else:
          end = int(rest[0])
          slice_object = slice(0, end)
      elif str.isnumeric(start):
        if not rest:
          op_ = int(start)
          slice_object = slice(op_, op_ + 1)
        elif rest == ['']:
          op_ = int(start)
          slice_object = slice(op_, None)
        else:
          op_ = int(start)
          end = int(rest[0])
          slice_object = slice(op_, end)
      return ProcessedField(
        field=field_name,
        customizer=Customizer(
          type='slice',
          value=SliceField(
            slice_literal=slice_object, value=re.sub(r'^.', '', slice_literal)
          ),
        ),
      )
    if len(resources := cls._extract_resource_element(raw_field)) > 1:
      field_name, resource_index = resources
      return ProcessedField(
        field=field_name,
        customizer=Customizer(type='resource_index', value=int(resource_index)),
      )

    if len(nested_fields := cls._extract_nested_resource(raw_field)) > 1:
      field_name, nested_field = nested_fields
      return ProcessedField(
        field=field_name,
        customizer=Customizer(type='nested_field', value=nested_field),
      )
    return ProcessedField(field=raw_field)

  @classmethod
  def _extract_resource_element(cls, line_elements: str) -> list[str]:
    return re.split('~', line_elements)

  @classmethod
  def _extract_slices(cls, line_elements: str) -> list[str]:
    """Finds all slices in the query line."""
    pattern = r'\[\d*(:\d*)?\]'
    slices = re.split(pattern, line_elements)
    regexp = r'\[(\d*(:\d*)?)\]'
    op = re.findall(regexp, line_elements)
    if op:
      slices[1] = op[0][0]
    return slices

  @classmethod
  def _extract_nested_resource(cls, line_elements: str) -> list[str]:
    if '://' in line_elements:
      return []
    return re.split(':', line_elements)


class VirtualColumn(pydantic.BaseModel):
  """Represents element in Garf query that either calculated or plugged-in.

  Virtual columns allow performing basic manipulation with metrics and
  dimensions (i.e. division or multiplication) as well as adding raw text
  values directly into report.

  Attributes:
    type: Type of virtual column, either build-in or expression.
    value: Value of the field after macro expansion.
    fields: Possible fields participating in calculations.
    substitute_expression: Formatted expression.
  """

  type: str
  value: str | int | float
  fields: list[str] | None = None
  substitute_expression: str | None = None

  @classmethod
  def from_raw(cls, field: str, macros: QueryParameters) -> VirtualColumn:
    """Converts a field to virtual column."""
    if field.isdigit():
      field = int(field)
    else:
      with contextlib.suppress(ValueError):
        field = float(field)
    if isinstance(field, (int, float)):
      return VirtualColumn(type='built-in', value=field)

    operators = ('/', r'\*', r'\+', ' - ')
    if '://' in field:
      expressions = re.split(r'\+', field)
    else:
      expressions = re.split('|'.join(operators), field)
    if len(expressions) > 1:
      virtual_column_fields = []
      substitute_expression = field
      for expression in expressions:
        element = expression.strip()
        if not _is_constant(element):
          virtual_column_fields.append(element)
          substitute_expression = substitute_expression.replace(
            element, f'{{{element}}}'
          )
      pattern = r'\{([^}]*)\}'
      substitute_expression = re.sub(
        pattern, lambda m: m.group(0).replace('.', '_'), substitute_expression
      )
      return VirtualColumn(
        type='expression',
        value=field.format(**macros) if macros else field,
        fields=virtual_column_fields,
        substitute_expression=substitute_expression,
      )
    if not _is_quoted_string(field):
      raise GarfFieldError(f"Incorrect field '{field}'.")
    field = field.replace("'", '').replace('"', '')
    field = field.format(**macros) if macros else field
    return VirtualColumn(type='built-in', value=field)


class ExtractedLineElements(pydantic.BaseModel):
  """Helper class for parsing query lines.

  Attributes:
    fields: All fields extracted from the line.
    alias: Optional alias assign to a field.
    virtual_column: Optional virtual column extracted from query line.
    customizer: Optional values for customizers associated with a field.
  """

  field: str | None
  alias: str | None
  virtual_column: VirtualColumn | None = None
  customizer: Customizer | None = None

  @classmethod
  def from_query_line(
    cls,
    line: str,
    macros: QueryParameters | None = None,
  ) -> ExtractedLineElements:
    if macros is None:
      macros = {}
    field, *alias = re.split(' [Aa][Ss] ', line)
    processed_field = ProcessedField.from_raw(field)
    field = processed_field.field
    virtual_column = (
      VirtualColumn.from_raw(field, macros)
      if _is_invalid_field(field)
      else None
    )
    if not (customizer := processed_field.customizer):
      customizer = None
    if virtual_column and not alias:
      raise GarfVirtualColumnError(
        f'Virtual attributes should be aliased: {virtual_column.value}'
      )
    return ExtractedLineElements(
      field=_format_type_field_name(field)
      if not virtual_column and field
      else None,
      alias=_normalize_column_name(alias[0] if alias else field),
      virtual_column=virtual_column,
      customizer=customizer,
    )


def _format_type_field_name(field_name: str) -> str:
  return re.sub(r'\.type', '.type_', field_name)


def _normalize_column_name(column_name: str) -> str:
  return re.sub(r'\.', '_', column_name)


def _is_quoted_string(field_name: str) -> bool:
  return (field_name.startswith("'") and field_name.endswith("'")) or (
    field_name.startswith('"') and field_name.endswith('"')
  )


def _is_constant(element) -> bool:
  with contextlib.suppress(ValueError):
    float(element)
    return True
  return _is_quoted_string(element)


def _is_invalid_field(field) -> bool:
  operators = ('/', '*', '+', ' - ')
  is_constant = _is_constant(field)
  has_operator = any(operator in field for operator in operators)
  return is_constant or has_operator
