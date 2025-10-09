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

import re
from typing import Literal, Union

import pydantic
from typing_extensions import TypeAlias

QueryParameters: TypeAlias = dict[str, Union[str, float, int, list]]

CustomizerType: TypeAlias = Literal[
  'resource_index', 'nested_field', 'pointer', 'slice'
]


class Customizer(pydantic.BaseModel):
  type: CustomizerType | None = None
  value: int | str | SliceField | None = None

  def __bool__(self) -> bool:
    return bool(self.type and self.value)


class SliceField(pydantic.BaseModel):
  model_config = pydantic.ConfigDict(arbitrary_types_allowed=True)
  sl: slice
  value: str | int


class ProcessedField(pydantic.BaseModel):
  """Stores field with its customizers.

  Attributes:
    field: Extractable field.
    customizer_type: Type of customizer to be applied to the field.
    customizer_value: Value to be used in customizer.
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
      field_name, op, sl = slices
      start, *rest = op.split(':')
      if start == '':
        if not rest:
          sl_obj = slice(None)
        else:
          end = int(rest[0])
          sl_obj = slice(0, end)
      elif str.isnumeric(start):
        if not rest:
          op_ = int(start)
          sl_obj = slice(op_, op_ + 1)
        elif rest == ['']:
          op_ = int(start)
          sl_obj = slice(op_, None)
        else:
          op_ = int(start)
          end = int(rest[0])
          sl_obj = slice(op_, end)
      return ProcessedField(
        field=field_name,
        customizer=Customizer(
          type='slice', value=SliceField(sl=sl_obj, value=re.sub(r'^.', '', sl))
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
    if len(pointers := cls._extract_pointer(raw_field)) > 1:
      field_name, pointer = pointers
      return ProcessedField(
        field=field_name,
        customizer=Customizer(type='pointer', value=pointer),
      )
    return ProcessedField(field=raw_field)

  @classmethod
  def _extract_resource_element(cls, line_elements: str) -> list[str]:
    return re.split('~', line_elements)

  @classmethod
  def _extract_slices(cls, line_elements: str) -> list[str]:
    pattern = r'\[\d*(:\d*)?\]'
    slices = re.split(pattern, line_elements)
    regexp = r'\[(\d*(:\d*)?)\]'
    op = re.findall(regexp, line_elements)
    if op:
      slices[1] = op[0][0]
    return slices

  @classmethod
  def _extract_pointer(cls, line_elements: str) -> list[str]:
    return re.split('->', line_elements)

  @classmethod
  def _extract_nested_resource(cls, line_elements: str) -> list[str]:
    if '://' in line_elements:
      return []
    return re.split(':', line_elements)


def _is_quoted_string(field_name: str) -> bool:
  return (field_name.startswith("'") and field_name.endswith("'")) or (
    field_name.startswith('"') and field_name.endswith('"')
  )
