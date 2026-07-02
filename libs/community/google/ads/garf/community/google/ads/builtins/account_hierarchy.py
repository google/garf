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
import functools
import operator
from collections import defaultdict

from garf.core.report import GarfReport


def get_account_hierarchy(
  report_fetcher: 'garf.community.google.ads.GoogleAdsApiReportFetcher',
  account: str | list[str],
  **kwargs: str,
) -> GarfReport:
  seed_accounts_query = """
    SELECT
        customer_client.level AS level,
        customer_client.manager AS is_manager,
        customer_client.id AS account_id
    FROM customer_client
    WHERE customer_client.level <= 1
    """

  nested_accounts_query = """
    SELECT
        customer.id AS mcc_id,
        customer.descriptive_name AS mcc_name,
        {level} AS level,
        customer_client_link.client_customer~0 AS account_id
    FROM customer_client_link
    """

  if isinstance(account, str):
    account = account.split(',')
  hierarchy = report_fetcher.fetch(
    query_specification=seed_accounts_query, account=account
  )
  level_mapping = defaultdict(list)
  for row in hierarchy:
    if row.is_manager:
      level_mapping[row.level].append(row.account_id)

  reports: list[GarfReport] = []
  for level, accounts in level_mapping.items():
    if accounts:
      reports.append(
        report_fetcher.fetch(
          query_specification=nested_accounts_query.format(level=level),
          account=accounts,
        )
      )

  combined_report = functools.reduce(operator.add, reports)
  df = combined_report.to_pandas()
  max_level = max(df.level)
  root_mcc_df = df[df.level == 0][['mcc_id', 'mcc_name', 'account_id']]
  root_mcc_df = root_mcc_df.rename(
    columns={'mcc_id': 'root_mcc_id', 'mcc_name': 'root_mcc_name'}
  )
  root_mcc_df['account_id'] = root_mcc_df['account_id'].astype(int)
  selectable_columns = ['root_mcc_id', 'root_mcc_name']
  if max_level == 0:
    return GarfReport.from_pandas(root_mcc_df)
  for i in range(1, max(df.level) + 1):
    if i == 1:
      n_mcc_df = df[df.level == i][['mcc_id', 'mcc_name', 'account_id']]
      mcc_ids = n_mcc_df.merge(
        root_mcc_df, how='right', left_on='mcc_id', right_on='account_id'
      )[
        [
          'root_mcc_id',
          'root_mcc_name',
          'account_id_x',
          'mcc_id',
          'mcc_name',
          'account_id_y',
        ]
      ]
    else:
      previous_level = i - 1
      n_minus_1_mcc_df = df[df.level == previous_level][
        ['mcc_id', 'mcc_name', 'account_id']
      ]
      n_minus_1_mcc_df = n_minus_1_mcc_df.rename(
        columns={
          'mcc_id': f'level_{previous_level}_mcc_id',
          'mcc_name': f'level_{previous_level}_mcc_name',
        }
      )
      mcc_ids = n_mcc_df.merge(
        n_minus_1_mcc_df, how='right', left_on='mcc_id', right_on='account_id'
      )[
        [
          f'level_{previous_level}_mcc_id',
          f'level_{previous_level}_mcc_name',
          'account_id_x',
          'mcc_id',
          'mcc_name',
          'account_id_y',
        ]
      ]

    mcc_ids.mcc_name.fillna('Direct', inplace=True)
    mcc_ids.account_id_x.fillna(mcc_ids.account_id_y, inplace=True)
    mcc_ids.mcc_id.fillna(mcc_ids.account_id_y, inplace=True)
    mcc_ids = mcc_ids.rename(
      columns={
        'mcc_name': f'level_{i}_mcc_name',
        'account_id_x': 'account_id',
        'mcc_id': f'level_{i}_mcc_id',
      }
    )[
      selectable_columns
      + [f'level_{i}_mcc_id', f'level_{i}_mcc_name', 'account_id']
    ]
    mcc_ids = mcc_ids.dropna()
    mcc_ids[f'level_{i}_mcc_id'] = mcc_ids[f'level_{i}_mcc_id'].astype(int)
  mcc_ids['account_id'] = mcc_ids['account_id'].astype(int)
  mcc_ids = mcc_ids.drop_duplicates()
  return GarfReport.from_pandas(mcc_ids)
