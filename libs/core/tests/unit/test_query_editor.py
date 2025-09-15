# Copyright 2024 Google LLC
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

from __future__ import annotations

import datetime

import pytest
from garf_core import query_editor


@pytest.fixture
def query():
  return """
-- Comment
# Comment
// Comment
/* Multiline
comment
*/

SELECT
    1 AS constant,
    '2023-01-01' AS date,
    '{current_date}' AS current_date,
    metrics.clicks / metrics.impressions AS ctr,
    customer.id, -- Inline comment
    campaign.bidding_strategy_type AS campaign_type, campaign.id:nested AS campaign,
    ad_group.id~1 AS ad_group,
    ad_group_ad.ad.id->asset AS ad,
    metrics.cost_micros * 1e6 AS cost,
    {% if selective == "true" %}
        campaign.selective_optimization AS selective_optimization,
    {% endif %}
from ad_group_ad;
"""


class TestQuerySpecification:
  def test_generate_returns_correct(self, query):
    test_query_spec = query_editor.QuerySpecification(text=query)
    test_query_spec.generate()

    expected_query_elements = query_editor.BaseQueryElements(
      title=None,
      resource_name='ad_group_ad',
      text='',
      fields=[
        '1',
        "'2023-01-01'",
        f"'{datetime.date.today().strftime('%Y-%m-%d')}'",
        'metrics.clicks / metrics.impressions',
        'customer.id',
        'campaign.bidding_strategy_type',
        'campaign.id',
        'ad_group.id',
        'ad_group_ad.ad.id',
        'metrics.cost_micros * 1e6',
      ],
      column_names=[
        'constant',
        'date',
        'current_date',
        'ctr',
        'customer_id',
        'campaign_type',
        'campaign',
        'ad_group',
        'ad',
        'cost',
      ],
      customizers={
        'campaign': {'type': 'nested_field', 'value': 'nested'},
        'ad_group': {'type': 'resource_index', 'value': 1},
        'ad': {'type': 'pointer', 'value': 'asset'},
      },
      virtual_columns={},
    )

    assert test_query_spec.query == expected_query_elements

  def test_generate_returns_builtin_query(self):
    query = 'SELECT test FROM builtin.test'
    test_query_spec = query_editor.QuerySpecification(text=query, title='test')
    test_query_spec.generate()
    expected_query_elements = query_editor.BaseQueryElements(
      title='test',
      text=query,
      resource_name='builtin.test',
      is_builtin_query=True,
    )

    assert test_query_spec.query == expected_query_elements
