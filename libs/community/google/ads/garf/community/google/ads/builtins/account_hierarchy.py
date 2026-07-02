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

from typing import Any

from garf.core.report import GarfReport

# FIXME: hierarchy is available to level 1 only
# TODO: Add pairs mapping: account -> sub_account
# TODO: Add graph mapping- A:account{name, id, sub_accounts: list[A]}


def get_account_hierarchy(
  report_fetcher: 'garf.community.google.ads.GoogleAdsApiReportFetcher',
  account: str | list[str],
  level: int = 0,
  **kwargs: str,
) -> GarfReport:
  level_mapping = _fetch_account_hierarchy(report_fetcher, account, level)
  column_names = [
    'level',
    'mcc_id',
    'mcc_name',
    'account_id',
    'account_name',
    'is_manager',
  ]
  results = []
  for level_in_hierarchy, result in level_mapping.items():
    for row in result.get('mcc'):
      if row.get('manager_id') != row.get('account_id'):
        results.append(
          [
            row.get('level') + level_in_hierarchy,
            row.get('manager_id'),
            row.get('manager_name'),
            row.get('account_id'),
            row.get('account_name'),
            True,
          ]
        )
    for row in result.get('direct'):
      results.append(
        [
          row.get('level') + level_in_hierarchy,
          row.get('manager_id'),
          row.get('manager_name'),
          row.get('account_id'),
          row.get('account_name'),
          False,
        ]
      )
  return GarfReport(results=results, column_names=column_names)


def _fetch_account_hierarchy(
  report_fetcher: 'garf.community.google.ads.GoogleAdsApiReportFetcher',
  account: str | list[str],
  level: int = 0,
) -> dict[str, Any]:
  seed_accounts_query = """
    SELECT
      customer_client.level AS level,
      customer.descriptive_name AS manager_name,
      customer.id AS manager_id,
      customer_client.manager AS is_manager,
      {level} AS level_in_hierarchy,
      customer_client.id AS account_id,
      customer_client.descriptive_name AS account_name
    FROM customer_client
    WHERE
      customer_client.level <= 1
      AND customer_client.status = ENABLED
      AND customer_client.hidden = FALSE
    """

  if isinstance(account, str):
    account = account.split(',')
  hierarchy = report_fetcher.fetch(
    query_specification=seed_accounts_query.format(level=level), account=account
  )
  level_mapping = {}
  for level_in_hierarchy, accounts in hierarchy.to_dict(
    'level_in_hierarchy'
  ).items():
    mccs = []
    direct_accounts = []
    for row in accounts:
      if row.get('is_manager'):
        mccs.append(row)
      else:
        direct_accounts.append(row)
    level_mapping[level_in_hierarchy] = {'mcc': mccs, 'direct': direct_accounts}

  sub_mccs = level_mapping.get(level, {}).get('mcc')
  if sub_mccs and (
    accounts := {
      a.get('account_id')
      for a in sub_mccs
      if a.get('account_id') != a.get('manager_id')
    }
  ):
    result = _fetch_account_hierarchy(
      report_fetcher, account=accounts, level=level + 1
    )
    level_mapping.update(result)
  return level_mapping
