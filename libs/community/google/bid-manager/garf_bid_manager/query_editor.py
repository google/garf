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

import logging
import re

from garf_core import query_editor, query_parser
from typing_extensions import Self

logger = logging.getLogger(__name__)


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
      field_lower = field.lower()
      if field_lower.startswith('datarange'):
        if 'in' in field_lower:
          values = re.findall(r'\((.*?)\)', field)
          if not (values := values[0]):
            raise query_parser.GarfQueryError(
              'No values in IN dataRange statement: ' + field
            )
          start_date, *end_date = values.split(',')
          if not end_date:
            logger.warning(
              'End date is not specified in query, setting to today.'
            )
            end_date = query_editor.CommonParametersMixin().common_params.get(
              'current_date'
            )
          else:
            end_date = end_date[0]

          filters.append(f'dataRange.customStartDate = {start_date.strip()}')
          filters.append(f'dataRange.customEndDate = {end_date.strip()}')
        else:
          filters.append(field)
      elif ' in ' in field_lower:
        filter_name, *rest = field_lower.split(' in ')
        values = re.findall(r'\((.*?)\)', field)
        if not (values := values[0]):
          raise query_parser.GarfQueryError(
            'No values in IN statement: ' + field
          )
        for value in values.split(','):
          filter_name = filter_name.strip()
          filter_value = value.strip()
          filters.append(_normalize_filter(f'{filter_name} = {filter_value}'))
      else:
        filters.append(_normalize_filter(field))
    self.query.filters = filters
    return self


def _normalize_field(field: str) -> str:
  if re.match('^(metric|filter)_*', field.lower(), re.IGNORECASE):
    return field.upper()
  return f'FILTER_{field.upper()}'


def _normalize_filter(field: str) -> str:
  name, operator, *value = field.split()
  value = ' '.join(value)
  if re.match('^(metric|filter)_*', name.lower(), re.IGNORECASE):
    return f'{name.upper()} {operator} {value}'
  return f'FILTER_{name.upper()} {operator} {value}'
