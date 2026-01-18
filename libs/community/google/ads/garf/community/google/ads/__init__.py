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

"""Library for getting reports from Google Ads & Search Ads 360 API."""

from garf.community.google.ads.api_clients import (
  GoogleAdsApiClient,
  SearchAds360ApiClient,
)
from garf.community.google.ads.report_fetcher import (
  GoogleAdsApiReportFetcher,
  SearchAds360ApiReportFetcher,
)

__all__ = [
  'GoogleAdsApiClient',
  'GoogleAdsApiReportFetcher',
  'SearchAds360ApiClient',
  'SearchAds360ApiReportFetcher',
]

__version__ = '1.1.0'
