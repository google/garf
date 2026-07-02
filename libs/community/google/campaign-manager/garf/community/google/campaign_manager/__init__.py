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

"""Library for getting reports from Campaign Manager 360 API."""

from garf.community.google.campaign_manager.api_clients import (
  CampaignManager360ApiClient,
)
from garf.community.google.campaign_manager.report_fetcher import (
  CampaignManager360ApiReportFetcher,
)

__all__ = [
  'CampaignManager360ApiClient',
  'CampaignManager360ApiReportFetcher',
]
