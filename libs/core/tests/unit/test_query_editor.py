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
from dateutil.relativedelta import relativedelta
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
    'http://youtube.com/watch?v=' + video.video_id AS video_url,
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
        'customer.id',
        'campaign.bidding_strategy_type',
        'campaign.id',
        'ad_group.id',
        'ad_group_ad.ad.id',
        'metrics.clicks',
        'metrics.impressions',
        'metrics.cost_micros',
        'video.video_id',
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
        'video_url',
      ],
      customizers={
        'campaign': {'type': 'nested_field', 'value': 'nested'},
        'ad_group': {'type': 'resource_index', 'value': 1},
        'ad': {'type': 'pointer', 'value': 'asset'},
      },
      virtual_columns={
        'constant': query_editor.VirtualColumn(type='built-in', value=1),
        'date': query_editor.VirtualColumn(type='built-in', value='2023-01-01'),
        'current_date': query_editor.VirtualColumn(
          type='built-in', value=datetime.date.today().strftime('%Y-%m-%d')
        ),
        'ctr': query_editor.VirtualColumn(
          type='expression',
          value='metrics.clicks / metrics.impressions',
          fields=['metrics.clicks', 'metrics.impressions'],
          substitute_expression='{metrics_clicks} / {metrics_impressions}',
        ),
        'cost': query_editor.VirtualColumn(
          type='expression',
          value='metrics.cost_micros * 1e6',
          fields=['metrics.cost_micros'],
          substitute_expression='{metrics_cost_micros} * 1e6',
        ),
        'video_url': query_editor.VirtualColumn(
          type='expression',
          value="'http://youtube.com/watch?v=' + video.video_id",
          fields=['video.video_id'],
          substitute_expression=(
            "'http://youtube.com/watch?v=' + {video_video_id}"
          ),
        ),
      },
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

  def test_generate_returns_macros(self):
    query = 'SELECT test FROM resource WHERE start_date = {start_date}'
    test_query_spec = query_editor.QuerySpecification(
      text=query,
      title='test',
      args=query_editor.GarfQueryParameters(
        macro={'start_date': ':YYYYMMDD'},
      ),
    )
    assert test_query_spec.macros.get(
      'start_date'
    ) == datetime.date.today().strftime('%Y-%m-%d')


def test_convert_date_returns_correct_datestring():
  current_date = datetime.datetime.today()
  current_year = datetime.datetime(current_date.year, 1, 1)
  current_month = datetime.datetime(current_date.year, current_date.month, 1)
  last_year = current_year - relativedelta(years=1)
  last_month = current_month - relativedelta(months=1)
  yesterday = current_date - relativedelta(days=1)
  tomorrow = current_date + relativedelta(days=1)
  next_month = current_month + relativedelta(months=1)
  next_year = current_year + relativedelta(years=1)

  non_macro_date = '2022-01-01'
  date_year = ':YYYY'
  date_month = ':YYYYMM'
  date_day = ':YYYYMMDD'
  date_year_minus_one = ':YYYY-1'
  date_month_minus_one = ':YYYYMM-1'
  date_day_minus_one = ':YYYYMMDD-1'
  date_day_plus_one = ':YYYYMMDD+1'
  date_month_plus_one = ':YYYYMM+1'
  date_year_plus_one = ':YYYY+1'

  non_macro_date_converted = query_editor.convert_date(non_macro_date)
  new_date_year = query_editor.convert_date(date_year)
  new_date_month = query_editor.convert_date(date_month)
  new_date_day = query_editor.convert_date(date_day)
  new_date_year_minus_one = query_editor.convert_date(date_year_minus_one)
  new_date_month_minus_one = query_editor.convert_date(date_month_minus_one)
  new_date_day_minus_one = query_editor.convert_date(date_day_minus_one)
  new_date_day_plus_one = query_editor.convert_date(date_day_plus_one)
  new_date_month_plus_one = query_editor.convert_date(date_month_plus_one)
  new_date_year_plus_one = query_editor.convert_date(date_year_plus_one)

  assert non_macro_date_converted == non_macro_date
  assert new_date_year == current_year.strftime('%Y-%m-%d')
  assert new_date_month == current_month.strftime('%Y-%m-%d')
  assert new_date_day == current_date.strftime('%Y-%m-%d')
  assert new_date_year_minus_one == last_year.strftime('%Y-%m-%d')
  assert new_date_month_minus_one == last_month.strftime('%Y-%m-%d')
  assert new_date_day_minus_one == yesterday.strftime('%Y-%m-%d')
  assert new_date_day_plus_one == tomorrow.strftime('%Y-%m-%d')
  assert new_date_month_plus_one == next_month.strftime('%Y-%m-%d')
  assert new_date_year_plus_one == next_year.strftime('%Y-%m-%d')


@pytest.mark.parametrize('date', [':YYYYMMDD-N', ':YYYYMMDD-2-3', ':YYYMMDD'])
def test_convert_date_raise_garf_macro_error(date):
  with pytest.raises(query_editor.GarfMacroError):
    query_editor.convert_date(date)
