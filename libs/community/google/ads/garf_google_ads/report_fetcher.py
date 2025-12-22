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

"""Defines report fetcher for Google Ads API."""

import asyncio
import functools
import operator

import garf_core

from garf_google_ads import GoogleAdsApiClient, builtins, parsers, query_editor


class GoogleAdsApiReportFetcher(garf_core.ApiReportFetcher):
  """Defines report fetcher."""

  def __init__(
    self,
    api_client: GoogleAdsApiClient | None = None,
    parser: garf_core.parsers.ProtoParser = parsers.GoogleAdsRowParser,
    query_spec: query_editor.GoogleAdsApiQuery = (
      query_editor.GoogleAdsApiQuery
    ),
    builtin_queries=builtins.BUILTIN_QUERIES,
    parallel_threshold: int = 10,
    **kwargs: str,
  ) -> None:
    """Initializes GoogleAdsApiReportFetcher."""
    if not api_client:
      api_client = GoogleAdsApiClient(**kwargs)
    self.parallel_threshold = parallel_threshold
    super().__init__(api_client, parser, query_spec, builtin_queries, **kwargs)

  def fetch(
    self,
    query_specification: str | query_editor.GoogleAdsApiQuery,
    args: garf_core.query_editor.GarfQueryParameters | None = None,
    account: str | list[str] | None = None,
    expand_mcc: bool = False,
    customer_ids_query: str | None = None,
    **kwargs: str,
  ) -> garf_core.GarfReport:
    """Fetches data from Google Ads API.

    Args:
      query_specifiction: Query to execute.
      args: Optional parameters to fine-tune the query.
      account: Account(s) to get data from.
      expand_mcc: Whether to perform account expansion (MCC to Account).
      custom_ids_query: Query to reduce number of accounts based a condition.

    Returns:
      Fetched report for provided accounts.
    """
    if isinstance(account, str):
      account = account.split(',')
    if not args:
      args = {}
    if expand_mcc or customer_ids_query:
      account = self.expand_mcc(
        customer_ids=account, customer_ids_query=customer_ids_query
      )
    if len(account) == 1:
      return super().fetch(
        query_specification=query_specification,
        args=args,
        account=str(account[0]),
        **kwargs,
      )
    reports = asyncio.run(
      self._process_accounts(
        query=query_specification,
        account=account,
        args=args,
      )
    )
    return functools.reduce(operator.add, reports)

  async def _process_accounts(
    self,
    query,
    account: list[str],
    args,
  ):
    semaphore = asyncio.Semaphore(value=self.parallel_threshold)

    async def run_with_semaphore(fn):
      async with semaphore:
        return await fn

    tasks = [
      self.afetch(query_specification=query, account=str(acc), args=args)
      for acc in account
    ]
    return await asyncio.gather(*(run_with_semaphore(task) for task in tasks))

  def expand_mcc(
    self,
    customer_ids: str | list[str],
    customer_ids_query: str | None = None,
  ) -> list[str]:
    """Performs Manager account(s) expansion to child accounts.

    Args:
      customer_ids: Manager account(s) to be expanded.
      customer_ids_query: GAQL query used to reduce the number of customer_ids.

    Returns:
      All child accounts under provided customer_ids.
    """
    return self._get_customer_ids(
      seed_customer_ids=customer_ids, customer_ids_query=customer_ids_query
    )

  def _get_customer_ids(
    self,
    seed_customer_ids: str | list[str],
    customer_ids_query: str | None = None,
  ) -> list[str]:
    """Gets list of customer_ids from an MCC account.

    Args:
      seed_customer_ids: MCC account_id(s).
      customer_ids_query: GAQL query used to reduce the number of customer_ids.

    Returns:
      All customer_ids from MCC satisfying the condition.
    """
    query = """
        SELECT customer_client.id FROM customer_client
        WHERE customer_client.manager = FALSE
        AND customer_client.status = ENABLED
        AND customer_client.hidden = FALSE
        """
    if isinstance(seed_customer_ids, str):
      seed_customer_ids = seed_customer_ids.split(',')
    child_customer_ids = self.fetch(
      query_specification=query, account=seed_customer_ids
    ).to_list()
    if customer_ids_query:
      child_customer_ids = self.fetch(
        query_specification=customer_ids_query,
        account=[str(a) for a in child_customer_ids],
      )
      child_customer_ids = [
        row[0] if isinstance(row, garf_core.report.GarfRow) else row
        for row in child_customer_ids
      ]

    return list(
      {
        str(customer_id)
        for customer_id in child_customer_ids
        if customer_id != 0
      }
    )
