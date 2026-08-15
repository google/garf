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

"""Tests for OpenWeatherApiReportFetcher."""

import pytest
from garf.community.common_apis.openweather.report_fetcher import (
  OpenWeatherApiReportFetcher,
)
from garf.core.api_clients import FakeApiClient
from garf.core.report_fetcher import ApiReportFetcherError


@pytest.fixture
def fetcher():
  data = [{'name': 'Houston', 'main': {'temp': 302, 'humidity': 75}}]
  return OpenWeatherApiReportFetcher(api_client=FakeApiClient(results=data))


def test_alias():
  assert OpenWeatherApiReportFetcher.alias == 'openweather'


def test_fetcher_requires_api_key():
  with pytest.raises(ApiReportFetcherError, match='api_key'):
    OpenWeatherApiReportFetcher()


def test_fetch_returns_report(fetcher):
  report = fetcher.fetch(
    'SELECT name AS city, main.temp AS temperature FROM weather WHERE lat=0 AND lon=0'
  )
  assert report.column_names == ['city', 'temperature']
  assert report[0][0] == 'Houston'
  assert report[0][1] == 302
