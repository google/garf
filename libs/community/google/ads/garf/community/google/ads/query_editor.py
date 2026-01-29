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

from garf.core import query_editor


class GoogleAdsApiQuery(query_editor.QuerySpecification):
  """Query to Google Ads API."""

  def generate(self):
    base_query = super().generate()
    if not base_query.resource_name:
      raise query_editor.GarfResourceError(
        f'No resource found in query: {base_query.text}'
      )
    for field in base_query.fields:
      field = _format_type_field_name(field)
    for customizer in base_query.customizers.values():
      if customizer.type == 'nested_field':
        customizer.value = _format_type_field_name(customizer.value)
    return base_query


def _format_type_field_name(query: str) -> str:
  if query == 'type':
    return 'type_'
  return re.sub(r'\.type', '.type_', query)
