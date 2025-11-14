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

import pytest
from garf_bid_manager import api_clients, query_editor


@pytest.mark.parametrize(
  ('data_range', 'expected'),
  [
    (
      ' = LAST_7_DAYS',
      {'dataRange': {'range': 'LAST_7_DAYS'}},
    ),
    (
      ' IN (2025-01-01, 2025-01-31)',
      {
        'dataRange': {
          'range': 'CUSTOM_DATES',
          'customStartDate': {'year': 2025, 'month': 1, 'day': 1},
          'customEndDate': {'year': 2025, 'month': 1, 'day': 31},
        }
      },
    ),
  ],
)
def test_build_request(data_range, expected):
  query = f"""
    SELECT
    filter_advertiser_name AS advertiser_name,
    advertiser AS advertiser,
    metric_impressions AS impressions,
    FROM standard
    WHERE advertiser = 1
    AND dataRange {data_range}
    """
  spec = query_editor.BidManagerApiQuery(text=query, title='test').generate()

  api_request = api_clients._build_request(spec)

  expected_request = {
    'metadata': {
      'title': 'test',
      'dataRange': expected.get('dataRange'),
      'format': 'CSV',
    },
    'params': {
      'type': 'STANDARD',
      'groupBys': [
        'FILTER_ADVERTISER_NAME',
        'FILTER_ADVERTISER',
      ],
      'filters': [{'type': 'FILTER_ADVERTISER', 'value': '1'}],
      'metrics': [
        'METRIC_IMPRESSIONS',
      ],
    },
    'schedule': {'frequency': 'ONE_TIME'},
  }

  assert api_request == expected_request


def test_process_api_response():
  data = [
    'value1,value2,value3',
    'value1,"value1.5,value2.5",value3',
  ]
  result = api_clients._process_api_response(data, ['one', 'two', 'three'])

  expected_result = [
    {'one': 'value1', 'two': 'value2', 'three': 'value3'},
    {'one': 'value1', 'two': 'value1.5,value2.5', 'three': 'value3'},
  ]

  assert result == expected_result
