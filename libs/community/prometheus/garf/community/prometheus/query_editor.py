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


"""Formats Garf Prometheus query for simplified API requests."""

import re
from typing import override

import dateutil
from garf.core import query_editor


class PrometheusApiQuery(query_editor.QuerySpecification):
  """Query to Prometheus API."""

  @override
  def generate(self):
    query = super().generate()
    updated_filters = {}
    for filter_statement in query.filters:
      key, value = filter_statement.split('=')
      if re.match('^(start|end).*$', key):
        value = value.strip().replace(' ', '')
        formatted_datetime = dateutil.parser.parse(value).strftime(
          '%Y-%m-%dT%H:%M:%S.000Z'
        )
        updated_filters[key.strip()] = formatted_datetime
      else:
        updated_filters[key.strip()] = value.strip()
    query.filters = updated_filters
    return query
