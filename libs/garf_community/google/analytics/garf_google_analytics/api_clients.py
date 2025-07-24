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

from collections import defaultdict

from google.analytics.data_v1beta import BetaAnalyticsDataClient
from google.analytics.data_v1beta.types import (
  DateRange,
  Dimension,
  Metric,
  RunReportRequest,
)
from typing_extensions import override

from garf_core import api_clients, query_editor


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
    request = RunReportRequest(
      property=f'properties/{property_id}',
      dimensions=[Dimension(name='country')],
      metrics=[Metric(name='activeUsers')],
      date_ranges=[DateRange(start_date='2020-09-01', end_date='2025-09-15')],
    )
    response = self.client.run_report(request)
    results = []
    dimension_headers = [header.name for header in response.dimension_headers]
    metric_headers = [header.name for header in response.metric_headers]
    for row in response.rows:
      response_row: dict[str, dict[str, str]] = defaultdict(dict)
      for header, value in zip(row.dimension_values, dimension_headers):
        response_row[header] = value.value
      for header, value in zip(row.metric_values, metric_headers):
        response_row[header] = value.value
      results.append(response_row)
    return api_clients.GarfApiResponse(results=results)
