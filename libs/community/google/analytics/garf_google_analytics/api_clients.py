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
"""Creates API client for Google Analytics API."""

import re
from collections import defaultdict

from garf_core import api_clients, query_editor
from google.analytics.data_v1beta import BetaAnalyticsDataClient
from google.analytics.data_v1beta.types import (
  DateRange,
  Dimension,
  Metric,
  RunReportRequest,
)
from typing_extensions import override


class GoogleAnalyticsApiClient(api_clients.BaseClient):
  def __init__(self) -> None:
    """Initializes GoogleAnalyticsApiClient."""
    self._client = None

  @property
  def client(self):
    if self._client:
      return self._client_
    return BetaAnalyticsDataClient()

  @override
  def get_response(
    self, request: query_editor.BaseQueryElements, **kwargs: str
  ) -> api_clients.GarfApiResponse:
    property_id = kwargs.get('property_id')
    dimensions = [
      Dimension(name=field.split('.')[1])
      for field in request.fields
      if field.startswith('dimension')
    ]
    metrics = [
      Metric(name=field.split('.')[1])
      for field in request.fields
      if field.startswith('metric')
    ]
    date_dimensions = {}
    date_pattern = r'\d{4}-\d{2}-\d{2}'
    for field in request.filters:
      if field.startswith('start_date'):
        date_dimensions['start_date'] = re.findall(date_pattern, field)[0]
      if field.startswith('end_date'):
        date_dimensions['end_date'] = re.findall(date_pattern, field)[0]

    analytics_request = RunReportRequest(
      property=f'properties/{property_id}',
      dimensions=dimensions,
      metrics=metrics,
      date_ranges=[DateRange(**date_dimensions)],
    )
    response = self.client.run_report(analytics_request)
    results = []
    dimension_headers = [header.name for header in response.dimension_headers]
    metric_headers = [header.name for header in response.metric_headers]
    for row in response.rows:
      response_row: dict[str, dict[str, str]] = defaultdict(dict)
      for value, header in zip(row.dimension_values, dimension_headers):
        response_row[f'dimension.{header}'] = value.value
      for value, header in zip(row.metric_values, metric_headers):
        response_row[f'metric.{header}'] = value.value
      results.append(response_row)
    return api_clients.GarfApiResponse(results=results)
