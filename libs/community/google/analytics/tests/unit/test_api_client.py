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

from garf.community.google.analytics import api_clients, query_editor


class TestGoogleAnalyticsApiClient:
  def test_build_request_is_buildable(self):
    query = """
      SELECT
        dimension.country,
        metrics.adClicks
      FROM core
      WHERE
        startDate = yesterday
        AND endDate = '2025-01-01'
        AND metric.adClicks > 1
        AND dimension.country BEGINS_WITH Ca
    """

    query_elements = query_editor.GoogleAnalyticsApiQuery(text=query).generate()
    test_request = api_clients.build_request(
      property_id=1, query_elements=query_elements
    )

    assert test_request.metric_filter
    assert test_request.dimension_filter
    assert test_request.date_ranges

  def test_build_request_generates_and_groups(self):
    query = """
      SELECT
        dimension.country,
        metrics.adClicks
      FROM core
      WHERE
        startDate = yesterday
        AND endDate = '2025-01-01'
        AND metric.adClicks > 1
        AND metric.adClicks < 10
        AND dimension.country BEGINS_WITH Ca
        AND dimension.country ENDS_WITH da
    """

    query_elements = query_editor.GoogleAnalyticsApiQuery(text=query).generate()
    test_request = api_clients.build_request(
      property_id=1, query_elements=query_elements
    )
    assert test_request.metric_filter.and_group
    assert test_request.dimension_filter.and_group

  def test_build_request_generates_not_group(self):
    query = """
      SELECT
        dimension.country,
        metric.adClicks
      FROM core
      WHERE
        startDate = yesterday
        AND endDate = '2025-01-01'
        AND metric.adClicks != 0
        AND dimension.country != Canada
    """

    query_elements = query_editor.GoogleAnalyticsApiQuery(text=query).generate()
    test_request = api_clients.build_request(
      property_id=1, query_elements=query_elements
    )

    assert test_request.metric_filter.not_expression
    assert test_request.dimension_filter.not_expression
