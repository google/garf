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
"""Defines Google Analytics API specific query parser."""

import re

from garf.community.google.analytics import exceptions
from garf.core import query_editor
from typing_extensions import Self


class GoogleAnalyticsApiQuery(query_editor.QuerySpecification):
  """Query to Google Analytics API."""

  def extract_filters(self) -> Self:
    super().extract_filters()
    filters = {}
    date_dimensions = {}
    metric_filters = []
    dimension_filters = []
    for field in self.query.filters:
      if match := re.match('^(start|end)Date .?= (.+)', field):
        date_type = match.group(1).strip()
        date_value = match.group(2).strip()
        date_dimensions[date_type + '_date'] = _normalize_date(date_value)
      elif match := re.match(r'^metrics?.(\w+) (=|>=|>|<|<=|!=) (.+)', field):
        metric_name = match.group(1).strip()
        metric_operator = match.group(2).strip()
        metric_value = match.group(3).strip()
        metric_filters.append(
          {
            'field_name': metric_name,
            'numeric_filter': {
              'operation': metric_operator,
              'value': _normalize_numeric(metric_value),
            },
          }
        )
      elif match := re.match(r'^dimensions?.(\w+) (=|!=|\w+) (.+)', field):
        dimension_name = match.group(1).strip()
        dimension_operator = match.group(2).strip()
        dimension_value = match.group(3).strip()
        if dimension_operator.lower() == 'in':
          dimension_filters.append(
            {
              'field_name': dimension_name,
              'in_list_filter': {
                'values': [
                  re.sub(r'\)|\(|\[|\[', '', _normalize_string(v)).strip()
                  for v in dimension_value.split(',')
                ],
              },
            }
          )
        else:
          dimension_filters.append(
            {
              'field_name': dimension_name,
              'string_filter': {
                'match_type': 'EXACT'
                if dimension_operator == '='
                else dimension_operator.upper(),
                'value': _normalize_string(dimension_value),
              },
            }
          )
    if date_dimensions:
      filters['date_dimensions'] = date_dimensions
    if metric_filters:
      filters['metric_filter'] = metric_filters
    if dimension_filters:
      filters['dimension_filter'] = dimension_filters
    self.query.filters = filters
    return self


def _normalize_numeric(numeric: str) -> str:
  """Parses numeric value as float or int."""
  pattern = r'^[-+]?\d+\.\d+$'
  if re.match(pattern, numeric):
    return {'float': float(numeric)}
  return {'int': int(numeric)}


def _normalize_date(date: str) -> str:
  date = re.sub('"|\'', '', date.replace(' ', ''))
  if date in ('yesterday', 'today') or date.endswith('daysAgo'):
    return date
  date_pattern = r'\d{4}-\d{2}-\d{2}'
  date = re.findall(date_pattern, date)
  if date:
    return date[0]
  raise exceptions.GoogleAnalyticsApiError(
    'Incorrect date format, expected either YYYY-MM-DD or '
    f'yesterday, today, or NdaysAgo, got {date}'
  )


def _normalize_string(string: str) -> str:
  return re.sub('"|\'', '', string).strip()
