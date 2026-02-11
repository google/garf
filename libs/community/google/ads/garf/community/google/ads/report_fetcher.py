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
import warnings

import garf.core
from garf.community.google.ads import (
  api_clients,
  builtins,
  exceptions,
  parsers,
  query_editor,
)
from garf.community.google.ads.telemetry import tracer
from opentelemetry import trace


class GoogleAdsApiReportFetcherError(exceptions.GoogleAdsApiError):
  """Report fetcher specific error."""


class GoogleAdsApiReportFetcher(garf.core.ApiReportFetcher):
  """Defines report fetcher for Google Ads API."""

  alias = 'google-ads'

  def __init__(
    self,
    api_client: api_clients.GoogleAdsApiClient | None = None,
    parser: garf.core.parsers.ProtoParser = parsers.GoogleAdsRowParser,
    query_spec: query_editor.GoogleAdsApiQuery = (
      query_editor.GoogleAdsApiQuery
    ),
    builtin_queries=builtins.BUILTIN_QUERIES,
    parallel_threshold: int = 10,
    **kwargs: str,
  ) -> None:
    """Initializes GoogleAdsApiReportFetcher."""
    if not api_client:
      api_client = api_clients.GoogleAdsApiClient(**kwargs)
    self.parallel_threshold = parallel_threshold
    super().__init__(
      api_client=api_client,
      parser=parser,
      query_specification_builder=query_spec,
      builtin_queries=builtin_queries,
      preprocessors={'account': self.expand_mcc},
      **kwargs,
    )

  def fetch(
    self,
    query_specification: str | query_editor.GoogleAdsApiQuery,
    args: garf.core.query_editor.GarfQueryParameters | None = None,
    account: str | list[str] | None = None,
    expand_mcc: bool = False,
    customer_ids_query: str | None = None,
    **kwargs: str,
  ) -> garf.core.GarfReport:
    """Fetches data from Google Ads API.

    Args:
      query_specification: Query to execute.
      args: Optional parameters to fine-tune the query.
      account: Account(s) to get data from.
      expand_mcc: Whether to perform account expansion (MCC to Account).
      customer_ids_query: Query to reduce number of accounts based a condition.

    Returns:
      Fetched report for provided accounts.

    Raises:
      GoogleAdsApiReportFetcherError: If not account provided or found.
    """
    if not account:
      raise GoogleAdsApiReportFetcherError(
        'Provide an account to get data from.'
      )
    if isinstance(account, str):
      account = account.replace('-', '')
      account = account.split(',')
    else:
      account = [str(a).replace('-', '') for a in account]
    if not args:
      args = {}
    if expand_mcc or customer_ids_query:
      account = self.expand_mcc(
        account=account, customer_ids_query=customer_ids_query
      )
      if not account:
        raise GoogleAdsApiReportFetcherError(
          'No account found satisfying the condition {customer_ids_query}.'
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

  @tracer.start_as_current_span('expand_mcc')
  def expand_mcc(
    self,
    account: str | list[str],
    customer_ids_query: str | None = None,
    customer_ids: str | list | None = None,
  ) -> list[str]:
    """Performs Manager account(s) expansion to child accounts.

    Args:
      account: Manager account(s) to be expanded.
      customer_ids_query: GAQL query used to reduce the number of customer_ids.
      customer_ids: Manager account(s) to be expanded.

    Returns:
      All child accounts under provided customer_ids.
    """
    span = trace.get_current_span()
    if customer_ids and not account:
      warnings.warn(
        '`customer_ids` is deprecated, used `account` instead',
        category=DeprecationWarning,
        stacklevel=2,
      )
      account = customer_ids
    query = """
        SELECT customer_client.id FROM customer_client
        WHERE customer_client.manager = FALSE
        AND customer_client.status = ENABLED
        AND customer_client.hidden = FALSE
        """
    if isinstance(account, str):
      seed_customer_ids = account.split(',')
    span.set_attribute('accounts.seed_accounts', seed_customer_ids)
    child_customer_ids = self.fetch(
      query_specification=query, account=seed_customer_ids
    ).to_list()
    if not child_customer_ids:
      raise GoogleAdsApiReportFetcherError(
        'No ENABLED accounts found under provided seed accounts '
        f'{seed_customer_ids}'
      )
    span.set_attribute('accounts.child_accounts', child_customer_ids)
    if customer_ids_query:
      span.set_attribute('accounts.customer_ids_query', customer_ids_query)
      child_customer_ids = self.fetch(
        query_specification=customer_ids_query,
        account=[str(a) for a in child_customer_ids],
      )
      if not child_customer_ids:
        raise GoogleAdsApiReportFetcherError(
          f'No accounts found satisfying the follow query: {customer_ids_query}'
        )
      child_customer_ids = [
        row[0] if isinstance(row, garf.core.report.GarfRow) else row
        for row in child_customer_ids
      ]
      span.set_attribute(
        'accounts.child_accounts_conditioned', len(child_customer_ids)
      )
    return list(
      {
        str(customer_id)
        for customer_id in child_customer_ids
        if customer_id != 0
      }
    )


class SearchAds360ApiReportFetcher(GoogleAdsApiReportFetcher):
  """Defines report fetcher for Search Ads 360 API."""

  alias = 'search-ads-360'

  def __init__(
    self,
    api_client: api_clients.SearchAds360ApiClient | None = None,
    **kwargs: str,
  ) -> None:
    """Initializes SearchAds360ApiReportFetcher."""
    if not api_client:
      api_client = api_clients.SearchAds360ApiClient(**kwargs)
    super().__init__(
      api_client=api_client,
      **kwargs,
    )
