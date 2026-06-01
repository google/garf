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
"""Defines Campaign Manager 360 API specific query parser."""

import logging
import re

from garf.core import query_editor, query_parser
from typing_extensions import Self

logger = logging.getLogger(__name__)


class CampaignManager360ApiQuery(query_editor.QuerySpecification):
  """Query to Campaign Manager 360 API."""

  def extract_filters(self) -> Self:
    super().extract_filters()
    filters = []
    for field in self.query.filters:
      field_lower = field.lower()
      if field_lower.startswith('daterange'):
        if 'in' in field_lower:
          values = re.findall(r'\((.*?)\)', field)
          if not (values := values[0]):
            raise query_parser.GarfQueryError(
              'No values in IN dateRange statement: ' + field
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

          filters.append(f'dateRange.startDate = {start_date.strip()}')
          filters.append(f'dateRange.endDate = {end_date.strip()}')
        else:
          filters.append(field)
      else:
        filters.append(field)
    self.query.filters = filters
    return self
