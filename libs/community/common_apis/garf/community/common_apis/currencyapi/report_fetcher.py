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

"""Report fetcher for CurrencyAPI (currencyapi.com)."""

from __future__ import annotations

import garf.core
from garf.community.common_apis.currencyapi import api_clients
from garf.core import parsers, report_fetcher


class CurrencyApiReportFetcher(garf.core.ApiReportFetcher):
  """garf source for CurrencyAPI (``--source currencyapi``).

  This source is a focused wrapper around the garf REST client that removes
  the boilerplate required when using ``--source rest`` against CurrencyAPI:

  - The base endpoint URL is built in.
  - The API key is sent as an HTTP header automatically — it never needs to
    appear in query files or URLs.
  - CurrencyAPI's nested response structure is flattened automatically.
    The raw response::

        {"data": {"USD": {"code": "USD", "value": 1.08}, "GBP": {...}}}

    becomes rows where you can simply ``SELECT code, value``.

  Compared to ``--source rest`` the queries are simpler::

      -- With --source rest you must handle auth, the endpoint, and JSON paths:
      SELECT data.{currency}.value AS rate
      FROM latest
      WHERE base_currency={base} AND currencies={currency} AND apikey={key}

      -- With --source currencyapi auth and flattening are handled for you:
      SELECT code, value AS rate
      FROM latest
      WHERE base_currency={base} AND currencies={currencies}

  CLI usage::

      garf rates.sql --source currencyapi \\
        --source.api_key=YOUR_KEY \\
        --macro.base_currency=EUR \\
        --macro.currencies=USD,GBP,JPY \\
        --output csv

  Python usage::

      from garf.community.common_apis.currencyapi import CurrencyApiReportFetcher

      fetcher = CurrencyApiReportFetcher(api_key='YOUR_KEY')
      report  = fetcher.fetch(
        'SELECT code, value AS rate FROM latest WHERE base_currency=EUR'
      )

  Args:
    api_client: Pre-built :class:`~garf.community.common_apis.currencyapi.\
api_clients.CurrencyApiClient` instance.  When omitted a client is created
      automatically from ``api_key`` and ``endpoint`` kwargs.
    parser: Parser class used to convert API rows.  Defaults to
      :class:`~garf.core.parsers.NumericConverterDictParser` so exchange rate
      values are returned as Python numbers.
    api_key: CurrencyAPI secret key (required when ``api_client`` is not
      provided).
    endpoint: Override the default API base URL.
    **kwargs: Additional keyword arguments forwarded to the underlying client.

  Raises:
    ApiReportFetcherError: When neither ``api_client`` nor ``api_key`` is
      provided.
  """

  alias = 'currencyapi'

  def __init__(
    self,
    api_client: api_clients.CurrencyApiClient | None = None,
    parser: type[parsers.BaseParser] = parsers.NumericConverterDictParser,
    **kwargs: str,
  ) -> None:
    if not api_client:
      if not kwargs.get('api_key'):
        raise report_fetcher.ApiReportFetcherError(
          'CurrencyApiReportFetcher requires an api_key. '
          'Pass --source.api_key=YOUR_KEY on the CLI or provide the '
          'api_key keyword argument.'
        )
      api_client = api_clients.CurrencyApiClient(**kwargs)
    super().__init__(
      api_client=api_client,
      parser=parser,
      **kwargs,
    )
