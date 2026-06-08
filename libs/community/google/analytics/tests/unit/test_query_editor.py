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

import pytest
from garf.community.google.analytics.query_editor import GoogleAnalyticsApiQuery


class TestGoogleAnalyticsApiQuery:
  @pytest.mark.parametrize(
    ('date', 'result'),
    [
      ('today', 'today'),
      ('yesterday', 'yesterday'),
      ('2daysAgo', '2daysAgo'),
      ('2025-01-01', '2025-01-01'),
      ('"2025-01-01"', '2025-01-01'),
    ],
  )
  def test_extract_filters_parses_dates(self, date, result):
    query = f"""
        SELECT
          metrics.adClicks
        FROM core
        WHERE
          startDate = {date}
          AND endDate = {date}
      """
    spec = GoogleAnalyticsApiQuery(text=query).generate()
    assert spec.filters == {
      'date_dimensions': {'start_date': result, 'end_date': result}
    }

  @pytest.mark.parametrize(
    ('metric', 'result'),
    [
      ('adClicks >= 0', ('adClicks', '>=', {'int': 0})),
      ('adClicks = 0.0', ('adClicks', '=', {'float': 0})),
    ],
  )
  def test_extract_filters_parses_metrics(self, metric, result):
    query = f"""
        SELECT
          metrics.adClicks
        FROM core
        WHERE
          metric.{metric}
      """
    spec = GoogleAnalyticsApiQuery(text=query).generate()
    metric_name, metric_operator, metric_value = result
    expected_result = {
      'metric_filter': [
        {
          'field_name': metric_name,
          'numeric_filter': {
            'operation': metric_operator,
            'value': metric_value,
          },
        }
      ]
    }
    assert spec.filters == expected_result

  @pytest.mark.parametrize(
    ('dimension', 'result'),
    [
      ('country = "Canada"', ('country', 'EXACT', 'Canada')),
      ('country BEGINS_WITH "Ca"', ('country', 'BEGINS_WITH', 'Ca')),
    ],
  )
  def test_extract_filters_parses_dimensions(self, dimension, result):
    query = f"""
        SELECT
          dimensions.country
        FROM core
        WHERE
          dimension.{dimension}
      """
    spec = GoogleAnalyticsApiQuery(text=query).generate()
    dimension_name, dimension_operator, dimension_value = result
    expected_result = {
      'dimension_filter': [
        {
          'field_name': dimension_name,
          'string_filter': {
            'match_type': dimension_operator,
            'value': dimension_value,
          },
        }
      ]
    }
    assert spec.filters == expected_result

  def test_extract_filters_parses_multiple_dimensions(self):
    query = """
        SELECT
          dimensions.country
        FROM core
        WHERE
          dimension.country = Canada
          AND dimension.device = Mobile
      """
    spec = GoogleAnalyticsApiQuery(text=query).generate()
    assert len(spec.filters.get('dimension_filter')) == 2
