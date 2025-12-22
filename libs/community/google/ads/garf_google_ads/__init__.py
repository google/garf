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

"""Library for getting reports from Google Ads API."""

from garf_google_ads.api_clients import GoogleAdsApiClient
from garf_google_ads.report_fetcher import GoogleAdsApiReportFetcher

__all__ = [
  'GoogleAdsApiClient',
  'GoogleAdsApiReportFetcher',
]

__version__ = '0.0.2'
