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

import datetime

import pytest
from garf_bid_manager.query_editor import BidManagerApiQuery
from garf_core import query_parser


class TestBidManagerApiQuery:
  def test_generate_returns_correct_query_elements(self):
    query = """
    SELECT
    filter_advertiser_name AS advertiser_name,
    advertiser AS advertiser,
    metric_impressions AS impressions,
    FROM standard
    WHERE advertiser = 1
    AND dataRange = LAST_7_DAYS
    AND line_item_type = Demand Gen
    AND line_item_id IN (1, 2)
    """
    spec = BidManagerApiQuery(text=query, title='test').generate()

    assert spec.fields == [
      'FILTER_ADVERTISER_NAME',
      'FILTER_ADVERTISER',
      'METRIC_IMPRESSIONS',
    ]

    assert spec.filters == [
      'FILTER_ADVERTISER = 1',
      'dataRange = LAST_7_DAYS',
      'FILTER_LINE_ITEM_TYPE = Demand Gen',
      'FILTER_LINE_ITEM_ID = 1',
      'FILTER_LINE_ITEM_ID = 2',
    ]

  def test_generate_returns_raises_error_on_missing_in_filter(self):
    query = """
    SELECT
    filter_advertiser_name AS advertiser_name,
    FROM standard
    WHERE advertiser = 1
    AND line_item_id IN ()
    """
    with pytest.raises(
      query_parser.GarfQueryError,
      match='No values in IN statement: line_item_id IN ()',
    ):
      BidManagerApiQuery(text=query, title='test').generate()

  @pytest.mark.parametrize(
    ('date_range', 'expected'),
    [
      (['2025-01-01', '2025-12-31'], ['2025-01-01', '2025-12-31']),
      (
        ['2025-01-01'],
        ['2025-01-01', datetime.date.today().strftime('%Y-%m-%d')],
      ),
    ],
  )
  def test_generate_returns_correct_custom_date_filter(
    self, date_range, expected
  ):
    data_range = ', '.join(date_range)
    query = f"""
    SELECT
    advertiser AS advertiser,
    metric_impressions AS impressions,
    FROM standard
    WHERE advertiser = 1
    AND dataRange IN ({data_range})
    """
    spec = BidManagerApiQuery(text=query, title='test').generate()

    assert spec.fields == [
      'FILTER_ADVERTISER',
      'METRIC_IMPRESSIONS',
    ]

    expected_start_date, expected_end_date = expected
    expected_filters = [
      'FILTER_ADVERTISER = 1',
      f'dataRange.customStartDate = {expected_start_date}',
      f'dataRange.customEndDate = {expected_end_date}',
    ]
    assert spec.filters == expected_filters
