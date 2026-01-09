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

"""Simulates response from Google Ads API based on a query."""

from __future__ import annotations

import logging
from typing import Any

import garf.core
from garf.community.google.ads import parsers, query_editor
from garf.community.google.ads.api_clients import GoogleAdsApiClient
from garf.core import simulator

logger = logging.getLogger(__name__)


class GoogleAdsApiSimulatorSpecification(simulator.SimulatorSpecification):
  """Google Ads API specific simulator specification."""


class GoogleAdsApiReportSimulator(simulator.ApiReportSimulator):
  def __init__(
    self,
    api_client: GoogleAdsApiClient | None = None,
    parser: garf.core.parsers.ProtoParser = parsers.GoogleAdsRowParser,
    query_spec: query_editor.GoogleAdsApiQuery = (
      query_editor.GoogleAdsApiQuery
    ),
    **kwargs: str,
  ) -> None:
    if not api_client:
      api_client = GoogleAdsApiClient(**kwargs)
    super().__init__(api_client, parser, query_spec)

  def _generate_random_values(
    self,
    response_types: dict[str, Any],
  ) -> dict[str, Any]:
    return self.api_client._get_google_ads_row()
