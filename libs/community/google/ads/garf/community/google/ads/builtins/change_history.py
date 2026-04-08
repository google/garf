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
import itertools
import logging
from typing import Final

import garf.core
import numpy as np
import pandas as pd
from garf.community.google.ads import exceptions

logger = logging.getLogger(__name__)


MAX_LOOKBACK_DAYS: Final[int] = 28


def _generate_default_dates() -> tuple[datetime.datetime, datetime.datetime]:
  today = datetime.datetime.today()
  end_date = today - datetime.timedelta(days=1)
  start_date = today - datetime.timedelta(days=MAX_LOOKBACK_DAYS)
  return start_date, end_date


class GarfGoogleAdsBuiltinQueryError(exceptions.GoogleAdsApiError):
  """Handles incorrect builtin queries."""


class DateRangeQuery(garf.core.base_query.BaseQuery):
  """Defines common class of queries with customizable date range."""

  def __init__(
    self, start_date: str | None = None, end_date: str | None = None
  ) -> None:
    """Replaces start and end date in query with supplied current_values."""
    today = datetime.datetime.today()
    default_start_date, default_end_date = _generate_default_dates()
    end_date_datetime = (
      default_end_date
      if not end_date
      else datetime.datetime.strptime(end_date, '%Y-%m-%d')
    )
    start_date_datetime = (
      default_start_date
      if not start_date
      else datetime.datetime.strptime(start_date, '%Y-%m-%d')
    )
    if (days := (today - start_date_datetime).days) > MAX_LOOKBACK_DAYS:
      raise GarfGoogleAdsBuiltinQueryError(
        f'Start date cannot be past {MAX_LOOKBACK_DAYS} days ago, '
        f'got {days} days'
      )
    if end_date_datetime > today:
      raise GarfGoogleAdsBuiltinQueryError('End date cannot be in the future')
    if start_date_datetime > end_date_datetime:
      raise GarfGoogleAdsBuiltinQueryError(
        'Start date cannot be greater than end date'
      )
    self.start_date = start_date_datetime.strftime('%Y-%m-%d')
    self.end_date = end_date_datetime.strftime('%Y-%m-%d')


class CampaignBudgets(DateRangeQuery):
  """Fetches budget values for active campaigns."""

  query_text = """
      SELECT
        campaign.id AS campaign_id,
        campaign_budget.amount_micros AS budget_amount
      FROM campaign
      WHERE
        segments.date >= '{start_date}'
        AND segments.date <= '{end_date}'
        AND metrics.impressions > 0
      """


class CampaignTargetCpas(DateRangeQuery):
  """Fetches budget values for active campaigns."""

  query_text = """
      SELECT
        campaign.id AS campaign_id,
        campaign.target_cpa.target_cpa_micros AS target_cpa
      FROM campaign
      WHERE
        segments.date >= '{start_date}'
        AND segments.date <= '{end_date}'
        AND metrics.impressions > 0
        AND campaign.bidding_strategy_type = TARGET_CPA
      """


class CampaignTargetRoas(DateRangeQuery):
  """Fetches budget values for active campaigns."""

  query_text = """
      SELECT
        campaign.id AS campaign_id,
        campaign.target_roas.target_roas AS target_roas
      FROM campaign
      WHERE
        segments.date >= '{start_date}'
        AND segments.date <= '{end_date}'
        AND metrics.impressions > 0
        AND campaign.bidding_strategy_type = TARGET_ROAS
      """


class TargetCpaChangesQuery(DateRangeQuery):
  query_text = """
      SELECT
        change_event.change_date_time AS change_date,
        campaign.id AS campaign_id,
        change_event.old_resource:campaign.target_cpa.target_cpa_micros
          AS old_target_cpa,
        change_event.new_resource:campaign.target_cpa.target_cpa_micros
          AS new_target_cpa
      FROM change_event
      WHERE
        change_event.change_date_time >= '{start_date}'
        AND change_event.change_date_time <= '{end_date}'
        AND change_event.change_resource_type IN (CAMPAIGN)
      LIMIT 10000
      """


class TargetRoasChangesQuery(DateRangeQuery):
  query_text = """
      SELECT
        change_event.change_date_time AS change_date,
        campaign.id AS campaign_id,
        change_event.old_resource:campaign.target_roas.target_roas
          AS old_target_roas,
        change_event.new_resource:campaign.target_roas.target_roas
          AS new_target_roas
      FROM change_event
      WHERE
        change_event.change_date_time >= '{start_date}'
        AND change_event.change_date_time <= '{end_date}'
        AND change_event.change_resource_type IN (CAMPAIGN)
      LIMIT 10000
      """


class BudgetChangesQuery(DateRangeQuery):
  query_text = """
      SELECT
        change_event.change_date_time AS change_date,
        campaign.id AS campaign_id,
        change_event.old_resource:campaign_budget.amount_micros
          AS old_budget_amount,
        change_event.new_resource:campaign_budget.amount_micros
          AS new_budget_amount
      FROM change_event
      WHERE
        change_event.change_date_time >= '{start_date}'
        AND change_event.change_date_time <= '{end_date}'
        AND change_event.change_resource_type IN (CAMPAIGN_BUDGET)
      LIMIT 10000
      """


def target_cpa_history(
  report_fetcher: 'garf.community.google.ads.report_fetcher.GoogleAdsApiReportFetcher',
  account: str | list[str],
  start_date: str | None = None,
  end_date: str | None = None,
  **kwargs: str,
):
  current_target_cpas = _get_target_cpa_static(
    report_fetcher, account, start_date, end_date
  )
  if not current_target_cpas:
    logger.debug('No TARGET_CPA campaigns found for account %s', account)
    return garf.core.GarfReport(
      results_placeholder=[['', 1, 0.0]],
      column_names=['day', 'campaign_id', 'target_cpa'],
    )
  target_cpa_changes = _get_target_cpa_changes(
    report_fetcher, account, start_date, end_date
  )
  placeholders = _prepare_placeholders(
    current_target_cpas, start_date=start_date, end_date=end_date
  )
  return _build_history_report(
    changes=target_cpa_changes,
    current_values=current_target_cpas,
    placeholders=placeholders,
    event_type='target_cpa',
  )


def target_roas_history(
  report_fetcher: 'garf.community.google.ads.report_fetcher.GoogleAdsApiReportFetcher',
  account: str | list[str],
  start_date: str | None = None,
  end_date: str | None = None,
  **kwargs: str,
):
  current_target_roass = _get_target_roas_static(
    report_fetcher, account, start_date, end_date
  )
  if not current_target_roass:
    logger.debug('No TARGET_ROAS campaigns found for account %s', account)
    return garf.core.GarfReport(
      results_placeholder=[['', 1, 0.0]],
      column_names=['day', 'campaign_id', 'target_roas'],
    )
  target_roas_changes = _get_target_roas_changes(
    report_fetcher, account, start_date, end_date
  )
  placeholders = _prepare_placeholders(
    current_target_roass, start_date=start_date, end_date=end_date
  )
  return _build_history_report(
    changes=target_roas_changes,
    current_values=current_target_roass,
    placeholders=placeholders,
    event_type='target_roas',
  )


def budget_history(
  report_fetcher: 'garf.community.google.ads.report_fetcher.GoogleAdsApiReportFetcher',
  account: str | list[str],
  start_date: str | None = None,
  end_date: str | None = None,
  **kwargs: str,
):
  current_budgets = _get_budgets_static(
    report_fetcher, account, start_date, end_date
  )
  changes = _get_budgets_changes(report_fetcher, account, start_date, end_date)
  placeholders = _prepare_placeholders(
    current_budgets, start_date=start_date, end_date=end_date
  )
  return _build_history_report(
    changes=changes,
    current_values=current_budgets,
    placeholders=placeholders,
    event_type='budget_amount',
  )


def _get_target_roas_static(
  report_fetcher, account, start_date, end_date
) -> garf.core.GarfReport:
  return report_fetcher.fetch(
    query_specification=CampaignTargetRoas(
      start_date=start_date,
      end_date=end_date,
    ),
    account=account,
  )


def _get_target_roas_changes(
  report_fetcher, account, start_date, end_date
) -> garf.core.GarfReport:
  return report_fetcher.fetch(
    query_specification=TargetRoasChangesQuery(
      start_date=start_date,
      end_date=end_date,
    ),
    account=account,
  )


def _get_target_cpa_static(
  report_fetcher, account, start_date, end_date
) -> garf.core.GarfReport:
  return report_fetcher.fetch(
    query_specification=CampaignTargetCpas(
      start_date=start_date,
      end_date=end_date,
    ),
    account=account,
  )


def _get_target_cpa_changes(
  report_fetcher, account, start_date, end_date
) -> garf.core.GarfReport:
  return report_fetcher.fetch(
    query_specification=TargetCpaChangesQuery(
      start_date=start_date,
      end_date=end_date,
    ),
    account=account,
  )


def _get_budgets_static(
  report_fetcher, account, start_date, end_date
) -> garf.core.GarfReport:
  return report_fetcher.fetch(
    query_specification=CampaignBudgets(
      start_date=start_date,
      end_date=end_date,
    ),
    account=account,
  )


def _get_budgets_changes(
  report_fetcher, account, start_date, end_date
) -> garf.core.GarfReport:
  return report_fetcher.fetch(
    query_specification=BudgetChangesQuery(
      start_date=start_date,
      end_date=end_date,
    ),
    account=account,
  )


def _build_history_report(
  changes: garf.core.GarfReport,
  current_values: garf.core.GarfReport,
  placeholders: pd.DataFrame,
  event_type: str,
) -> garf.core.GarfReport:
  event_history = _restore_event_history(
    placeholders,
    changes.to_pandas(),
    current_values.to_pandas(),
    event_type=event_type,
  )
  event_history.sort_values(by=['campaign_id', 'day'], inplace=True)
  return garf.core.GarfReport.from_pandas(event_history)


def _prepare_placeholders(
  campaigns: garf.core.GarfReport,
  start_date: datetime.date | None = None,
  end_date: datetime.date | None = None,
) -> pd.DataFrame:
  """Generates all possible combinations of dates and campaign_ids."""
  default_start_date, default_end_date = _generate_default_dates()
  start_date = start_date or default_start_date
  end_date = end_date or default_end_date
  dates = {
    date.strftime('%Y-%m-%d')
    for date in pd.date_range(start_date, end_date).to_pydatetime().tolist()
  }
  campaign_ids = campaigns['campaign_id'].to_list(
    row_type='scalar', distinct=True
  )
  placeholders = pd.DataFrame(
    data=list(itertools.product(campaign_ids, dates)),
    columns=['campaign_id', 'day'],
  )
  placeholders.sort_values(by=['campaign_id', 'day'], inplace=True)
  return placeholders


def _restore_event_history(
  placeholders: pd.DataFrame,
  change_history: pd.DataFrame,
  current_bids_budgets: pd.DataFrame,
  event_type: str,
) -> pd.DataFrame:
  """Restores gaps in change history for a single event_type.

  Args:
    placeholders:
      Contains all possible combinations of dates for set of campaigns.
    change_history:
      Contains only changes in bid and budget events.
    current_bids_budgets:
      Contains last observable values of bid and budgets.
    event_type:
      Specifies type of event to restore change history for.

  Returns:
    DataFrame with filled gaps in change history for a given event_type.
  """
  partial_history = _prepare_events(change_history, event_type)
  if not partial_history.empty:
    joined = pd.merge(
      placeholders, partial_history, on=['campaign_id', 'day'], how='left'
    )
    joined['filled_backward'] = joined.groupby('campaign_id')[
      'value_old'
    ].bfill()
    joined['filled_forward'] = joined.groupby('campaign_id')[
      'value_new'
    ].ffill()
    joined['filled_forward'] = joined['filled_forward'].fillna(
      joined.groupby('campaign_id')['filled_backward'].transform('first')
    )
    joined = pd.merge(
      joined, current_bids_budgets, on='campaign_id', how='left'
    )
    joined[event_type] = np.where(
      joined['filled_forward'].isnull(),
      joined[event_type],
      joined['filled_forward'],
    )
  else:
    joined = pd.merge(
      placeholders, current_bids_budgets, on='campaign_id', how='left'
    )
  if event_type != 'target_roas':
    joined[event_type] = joined[event_type].astype(int)
  return joined[['day', 'campaign_id', event_type]]


def _prepare_events(
  change_history: pd.DataFrame, event_type: str
) -> pd.DataFrame:
  """Exacts change history events only for a given event_type.

  Args:
    change_history: Contains only changes in bid and budget events.
    event_type: Specifies type of event filter by.

  Returns:
    DataFrame with subset of change history for a given event_type.
  """
  events = change_history.loc[
    (change_history[f'old_{event_type}'] > 0)
    & (change_history[f'new_{event_type}'] > 0)
  ]
  if not events.empty:
    events = _format_partial_event_history(events, event_type)
    logging.debug('%d %s events were found', len(events), event_type)
  else:
    logging.debug('no %s events were found', event_type)
  return events


def _format_partial_event_history(
  events: pd.DataFrame, event_type: str
) -> pd.DataFrame:
  """Performs renaming and selecting last value for the date.

  Args:
    events: Change history data.
    event_type: Type of event to perform the formatting by.
  """
  events.loc[:, ('day')] = events['change_date'].str.split(expand=True)[0]
  events = events.rename(
    columns={
      f'old_{event_type}': 'value_old',
      f'new_{event_type}': 'value_new',
    }
  )[['day', 'campaign_id', 'value_old', 'value_new']]
  return events.groupby(['day', 'campaign_id']).last()
