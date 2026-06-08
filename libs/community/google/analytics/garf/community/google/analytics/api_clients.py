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

from garf.community.google.analytics import query_editor
from garf.core import api_clients
from google.analytics.data_v1beta import BetaAnalyticsDataClient
from google.analytics.data_v1beta.types import (
  DateRange,
  Dimension,
  Filter,
  FilterExpression,
  Metric,
  NumericValue,
  RunReportRequest,
)
from typing_extensions import override

_NUMERIC_OPERATORS = {
  '>=': Filter.NumericFilter.Operation.GREATER_THAN_OR_EQUAL,
  '>': Filter.NumericFilter.Operation.GREATER_THAN,
  '<': Filter.NumericFilter.Operation.LESS_THAN,
  '=<': Filter.NumericFilter.Operation.LESS_THAN_OR_EQUAL,
  '=': Filter.NumericFilter.Operation.EQUAL,
  '==': Filter.NumericFilter.Operation.EQUAL,
}


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
    self, request: query_editor.GoogleAnalyticsApiQuery, **kwargs: str
  ) -> api_clients.GarfApiResponse:
    property_id = kwargs.get('property_id')
    analytics_request = build_request(
      property_id=property_id, query_elements=request
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


def build_request(
  property_id: str,
  query_elements: query_editor.GoogleAnalyticsApiQuery,
) -> RunReportRequest:
  dimensions = [
    Dimension(name=field.split('.')[1])
    for field in query_elements.fields
    if field.startswith('dimension')
  ]
  metrics = [
    Metric(name=field.split('.')[1])
    for field in query_elements.fields
    if field.startswith('metric')
  ]
  filters = query_elements.filters
  date_ranges = [DateRange(**filters.get('date_dimensions'))]
  request = RunReportRequest(
    property=f'properties/{property_id}',
    dimensions=dimensions,
    metrics=metrics,
    date_ranges=date_ranges,
  )
  if metric_filter := filters.get('metric_filter'):
    metric_filters = []
    for m in metric_filter:
      numeric_filter = m.get('numeric_filter')
      is_int = numeric_filter.get('value').get('int') is not None
      metric_filters.append(
        Filter(
          field_name=m.get('field_name'),
          numeric_filter=Filter.NumericFilter(
            operation=_NUMERIC_OPERATORS.get(numeric_filter.get('operation')),
            value=NumericValue(
              int64_value=numeric_filter.get('value').get('int')
            )
            if is_int
            else NumericValue(
              double_value=numeric_filter.get('value').get('float')
            ),
          ),
        )
      )
    request.metric_filter = FilterExpression(filter=metric_filters[0])

  if dimension_filter := filters.get('dimension_filter'):
    dimension_filters = []
    for d in dimension_filter:
      string_filter = d.get('string_filter')
      dimension_filters.append(
        Filter(
          field_name=m.get('field_name'),
          string_filter=Filter.StringFilter(
            match_type=Filter.StringFilter.MatchType[
              string_filter.get('match_type')
            ],
            value=string_filter.get('value'),
          ),
        )
      )
    request.dimension_filter = FilterExpression(filter=dimension_filters[0])
  return request
