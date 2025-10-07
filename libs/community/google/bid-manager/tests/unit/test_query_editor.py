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


from garf_bid_manager.query_editor import BidManagerApiQuery


class TestBidManagerApiQuery:
  def test_generate(self):
    query = """
    SELECT
    filter_advertiser_name AS advertiser_name,
    advertiser AS advertiser,
    metric_impressions AS impressions,
    FROM standard
    WHERE advertiser = 1
    AND dataRange = LAST_7_DAYS
    """
    spec = BidManagerApiQuery(text=query, title='test').generate()

    assert spec.resource_name == 'STANDARD'
    assert spec.fields == [
      'FILTER_ADVERTISER_NAME',
      'FILTER_ADVERTISER',
      'METRIC_IMPRESSIONS',
    ]

    assert spec.filters == ['FILTER_ADVERTISER = 1', 'dataRange = LAST_7_DAYS']
