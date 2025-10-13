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


from garf_bid_manager import api_clients, query_editor


def test_build_request():
  query = """
    SELECT
    filter_advertiser_name AS advertiser_name,
    advertiser AS advertiser,
    metric_impressions AS impressions,
    FROM standard
    WHERE advertiser = 1
    AND dataRange = LAST_7_DAYS
    """
  spec = query_editor.BidManagerApiQuery(text=query, title='test').generate()

  api_request = api_clients._build_request(spec)

  expected_request = {
    'metadata': {
      'title': 'test',
      'dataRange': {'range': 'LAST_7_DAYS'},
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
