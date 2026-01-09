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
import re

import garf_core


def get_ocid_mapping(
  report_fetcher: 'garf_google_ads.GoogleAdsApiReportFetcher',
  account: str | list[str],
  **kwargs: str,
):
  """Returns mapping between external customer_id and OCID parameter.

  OCID parameter is used to build links to Google Ads entities in UI.

  Args:
    report_fetcher: An instance of GoogleAdsApiReportFetcher.
    accounts: Google Ads accounts to get data on OCID mapping.

  Returns:
      Report with mapping between external customer_id and OCID parameter.
  """
  query = (
    'SELECT customer.id AS account_id, '
    'metrics.optimization_score_url  AS url FROM customer'
  )
  mapping = []
  if isinstance(account, str):
    account = account.split(',')
  for acc in account:
    if report := report_fetcher.fetch(query_specification=query, account=acc):
      for row in report:
        if ocid := re.findall(r'ocid=(\w+)', row.url):
          mapping.append([row.account_id, ocid[0]])
          break
      if not ocid:
        mapping.append([int(acc), '0'])
    else:
      mapping.append([int(acc), '0'])
  return garf_core.GarfReport(
    results=mapping,
    column_names=[
      'account_id',
      'ocid',
    ],
  )
