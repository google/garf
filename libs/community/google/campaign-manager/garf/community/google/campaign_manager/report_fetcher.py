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

"""Defines report fetcher for Campaign Manager 360 API."""

import garf.core
from garf.community.google.campaign_manager import (
  api_clients,
  exceptions,
  query_editor,
  version,
)


class CampaignManager360ApiReportFetcherError(
  exceptions.CampaignManager360ApiError
):
  """Report fetcher specific error."""


class CampaignManager360ApiReportFetcher(garf.core.ApiReportFetcher):
  """Defines report fetcher for Campaign Manager 360 API."""

  alias = 'campaign-manager'
  version = version.__version__

  def __init__(
    self,
    profile_id: str | None = None,
    api_client: api_clients.CampaignManager360ApiClient | None = None,
    parser: garf.core.parsers.DictParser = (
      garf.core.parsers.NumericConverterDictParser
    ),
    query_spec: query_editor.CampaignManager360ApiQuery = (
      query_editor.CampaignManager360ApiQuery
    ),
    parallel_threshold: int = 10,
    **kwargs: str,
  ) -> None:
    """Initializes CampaignManager360ApiReportFetcher."""
    if not api_client:
      api_client = api_clients.CampaignManager360ApiClient(
        profile_id=profile_id, **kwargs
      )
    self.parallel_threshold = parallel_threshold
    super().__init__(
      api_client=api_client,
      parser=parser,
      query_specification_builder=query_spec,
      preprocessors={'init': self._init_api_client},
      **kwargs,
    )

  def _init_api_client(self, **kwargs) -> str:
    return self.api_client.client
