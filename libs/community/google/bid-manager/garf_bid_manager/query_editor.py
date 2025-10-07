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
"""Defines Bid Manager API specific query parser."""

import re

from garf_core import query_editor
from typing_extensions import Self


class BidManagerApiQuery(query_editor.QuerySpecification):
  """Query to Bid Manager API."""

  def extract_resource_name(self) -> Self:
    super().extract_resource_name()
    self.query.resource_name = self.query.resource_name.upper()
    return self

  def extract_fields(self) -> Self:
    super().extract_fields()
    fields = []
    for field in self.query.fields:
      fields.append(_normalize_field(field))
    self.query.fields = fields
    return self

  def extract_filters(self) -> Self:
    super().extract_filters()
    filters = []
    for field in self.query.filters:
      if field.lower().startswith('datarange'):
        filters.append(field)
      else:
        filters.append(_normalize_field(field))
    self.query.filters = filters
    return self


def _normalize_field(field: str) -> str:
  if re.match('^(metric|filter)_*', field.lower(), re.IGNORECASE):
    return field.upper()
  return f'FILTER_{field.upper()}'
