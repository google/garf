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

"""Tests for CurrencyApiReportFetcher."""

import pytest
from garf.community.common_apis.currencyapi.report_fetcher import (
  CurrencyApiReportFetcher,
)
from garf.core.api_clients import FakeApiClient
from garf.core.report_fetcher import ApiReportFetcherError


@pytest.fixture
def fetcher():
  # Integer values avoid NumericConverterDictParser int-before-float truncation.
  data = [{'code': 'USD', 'value': 108}, {'code': 'GBP', 'value': 85}]
  return CurrencyApiReportFetcher(api_client=FakeApiClient(results=data))


def test_alias():
  assert CurrencyApiReportFetcher.alias == 'currencyapi'


def test_fetcher_requires_api_key():
  with pytest.raises(ApiReportFetcherError, match='api_key'):
    CurrencyApiReportFetcher()


def test_fetch_returns_report(fetcher):
  report = fetcher.fetch(
    'SELECT code, value AS rate FROM latest WHERE base_currency=EUR'
  )
  assert report.column_names == ['code', 'rate']
  rates = {row[0]: row[1] for row in report}
  assert rates == {'USD': 108, 'GBP': 85}
