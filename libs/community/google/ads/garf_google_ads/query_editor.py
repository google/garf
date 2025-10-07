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
"""Defines Google Ads API specific query parser."""

import re

from garf_core import query_editor


class GoogleAdsApiQuery(query_editor.QuerySpecification):
  """Query to Google Ads API."""

  def generate(self):
    base_query = super().generate()
    for field in base_query.fields:
      field = _format_type_field_name(field)
    for customizer in base_query.customizers.values():
      if customizer.type == 'nested_field':
        customizer.value = _format_type_field_name(customizer.value)
    base_query.text = self._create_gaql_query()
    return base_query

  def _create_gaql_query(
    self,
  ) -> str:
    """Generate valid GAQL query.

    Based on original query text, a set of field and virtual columns
    constructs new GAQL query to be sent to Ads API.

    Returns:
      Valid GAQL query.
    """
    virtual_fields = [
      field
      for name, column in self.query.virtual_columns.items()
      if column.type == 'expression'
      for field in column.fields
    ]
    fields = self.query.fields
    if virtual_fields:
      fields = self.query.fields + virtual_fields
    joined_fields = ', '.join(fields)
    if filters := self.query.filters:
      filter_conditions = ' AND '.join(filters)
      filters = f'WHERE {filter_conditions}'
    else:
      filters = ''
    if sorts := self.query.sorts:
      sort_conditions = ' AND '.join(sorts)
      sorts = f'ORDER BY {sort_conditions}'
    else:
      sorts = ''
    query_text = (
      f'SELECT {joined_fields} '
      f'FROM {self.query.resource_name} '
      f'{filters} {sorts}'
    )
    query_text = _unformat_type_field_name(query_text)
    return re.sub(r'\s+', ' ', query_text).strip()


def _unformat_type_field_name(query: str) -> str:
  if query == 'type_':
    return 'type'
  return re.sub(r'\.type_', '.type', query)


def _format_type_field_name(query: str) -> str:
  if query == 'type':
    return 'type_'
  return re.sub(r'\.type', '.type_', query)
