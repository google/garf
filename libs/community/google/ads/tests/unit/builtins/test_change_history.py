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

import datetime

import garf.community.google.ads
import garf.core
import pytest
from garf.community.google.ads.builtins import change_history


def _get_date_string(days_ago: int = 28):
  today = datetime.datetime.today()
  return (today - datetime.timedelta(days=days_ago)).strftime('%Y-%m-%d')


class TestDateRangeQuery:
  def test_init_raises_error_on_start_date_past_28_days(self):
    with pytest.raises(
      change_history.GarfGoogleAdsBuiltinQueryError,
      match='Start date cannot be past 28 days ago, got 29 days',
    ):
      change_history.DateRangeQuery(start_date=_get_date_string(29))

  def test_init_raises_error_on_end_date_in_future(self):
    with pytest.raises(
      change_history.GarfGoogleAdsBuiltinQueryError,
      match='End date cannot be in the future',
    ):
      change_history.DateRangeQuery(end_date=_get_date_string(-1))

  def test_init_raises_error_on_dates_mismatch(self):
    with pytest.raises(
      change_history.GarfGoogleAdsBuiltinQueryError,
      match='Start date cannot be greater than end date',
    ):
      change_history.DateRangeQuery(
        start_date=_get_date_string(1), end_date=_get_date_string(2)
      )


def test_budget_history(mocker):
  test_report = garf.core.GarfReport(
    results=[
      ['2026-04-02', 1, 1000, 2000],
      ['2026-04-05', 1, 2000, 2500],
    ],
    column_names=[
      'change_date',
      'campaign_id',
      'old_budget_amount',
      'new_budget_amount',
    ],
  )
  mocker.patch(
    'garf.community.google.ads.api_clients.GoogleAdsApiClient.__init__',
    return_value=None,
  )
  mocker.patch(
    'garf.community.google.ads.builtins.change_history._get_budgets_changes',
    return_value=test_report,
  )
  campaign_report = garf.core.GarfReport(
    results=[
      [1, 2500],
    ],
    column_names=[
      'campaign_id',
      'budget_amount',
    ],
  )
  mocker.patch(
    'garf.community.google.ads.builtins.change_history._get_budgets_static',
    return_value=campaign_report,
  )

  restored_history = change_history.budget_history(
    report_fetcher=garf.community.google.ads.report_fetcher.GoogleAdsApiReportFetcher(),
    account=None,
    start_date='2026-04-01',
    end_date='2026-04-07',
  )
  expected_report = garf.core.GarfReport(
    results=[
      ['2026-04-01', 1, 1000],
      ['2026-04-02', 1, 2000],
      ['2026-04-03', 1, 2000],
      ['2026-04-04', 1, 2000],
      ['2026-04-05', 1, 2500],
      ['2026-04-06', 1, 2500],
      ['2026-04-07', 1, 2500],
    ],
    column_names=[
      'day',
      'campaign_id',
      'budget_amount',
    ],
  )

  assert restored_history == expected_report


def test_target_cpa_history(mocker):
  test_report = garf.core.GarfReport(
    results=[
      ['2026-04-02', 1, 1000, 2000],
      ['2026-04-05', 1, 2000, 2500],
    ],
    column_names=[
      'change_date',
      'campaign_id',
      'old_target_cpa',
      'new_target_cpa',
    ],
  )
  mocker.patch(
    'garf.community.google.ads.api_clients.GoogleAdsApiClient.__init__',
    return_value=None,
  )
  mocker.patch(
    'garf.community.google.ads.builtins.change_history._get_target_cpa_changes',
    return_value=test_report,
  )
  campaign_report = garf.core.GarfReport(
    results=[
      [1, 2500],
    ],
    column_names=[
      'campaign_id',
      'target_cpa',
    ],
  )
  mocker.patch(
    'garf.community.google.ads.builtins.change_history._get_target_cpa_static',
    return_value=campaign_report,
  )

  restored_history = change_history.target_cpa_history(
    report_fetcher=garf.community.google.ads.report_fetcher.GoogleAdsApiReportFetcher(),
    account=None,
    start_date='2026-04-01',
    end_date='2026-04-07',
  )
  expected_report = garf.core.GarfReport(
    results=[
      ['2026-04-01', 1, 1000],
      ['2026-04-02', 1, 2000],
      ['2026-04-03', 1, 2000],
      ['2026-04-04', 1, 2000],
      ['2026-04-05', 1, 2500],
      ['2026-04-06', 1, 2500],
      ['2026-04-07', 1, 2500],
    ],
    column_names=[
      'day',
      'campaign_id',
      'target_cpa',
    ],
  )

  assert restored_history == expected_report


def test_target_roas_history(mocker):
  test_report = garf.core.GarfReport(
    results=[
      ['2026-04-02', 1, 1.0, 2000],
      ['2026-04-05', 1, 2000, 2.5],
    ],
    column_names=[
      'change_date',
      'campaign_id',
      'old_target_roas',
      'new_target_roas',
    ],
  )
  mocker.patch(
    'garf.community.google.ads.api_clients.GoogleAdsApiClient.__init__',
    return_value=None,
  )
  mocker.patch(
    'garf.community.google.ads.builtins.change_history._get_target_roas_changes',
    return_value=test_report,
  )
  campaign_report = garf.core.GarfReport(
    results=[
      [1, 2.5],
    ],
    column_names=[
      'campaign_id',
      'target_roas',
    ],
  )
  mocker.patch(
    'garf.community.google.ads.builtins.change_history._get_target_roas_static',
    return_value=campaign_report,
  )

  restored_history = change_history.target_roas_history(
    report_fetcher=garf.community.google.ads.report_fetcher.GoogleAdsApiReportFetcher(),
    account=None,
    start_date='2026-04-01',
    end_date='2026-04-07',
  )
  expected_report = garf.core.GarfReport(
    results=[
      ['2026-04-01', 1, 1.0],
      ['2026-04-02', 1, 2000],
      ['2026-04-03', 1, 2000],
      ['2026-04-04', 1, 2000],
      ['2026-04-05', 1, 2.5],
      ['2026-04-06', 1, 2.5],
      ['2026-04-07', 1, 2.5],
    ],
    column_names=[
      'day',
      'campaign_id',
      'target_roas',
    ],
  )

  assert restored_history == expected_report
