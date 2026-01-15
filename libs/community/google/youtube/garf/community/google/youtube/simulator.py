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

"""Simulates response from YouTube Data API based on a query."""

from __future__ import annotations

import logging
from typing import Any

from garf.community.google.youtube import YouTubeDataApiClient, query_editor
from garf.core import parsers, simulator

logger = logging.getLogger(__name__)


class YouTubeDataApiSimulatorSpecification(simulator.SimulatorSpecification):
  """YouTube Data API specific simulator specification."""


class YouTubeDataApiReportSimulator(simulator.ApiReportSimulator):
  def __init__(
    self,
    api_client: YouTubeDataApiClient | None = None,
    parser: parsers.DictParser = parsers.DictParser,
    query_spec: query_editor.YouTubeDataApiQuery = (
      query_editor.YouTubeDataApiQuery
    ),
  ) -> None:
    if not api_client:
      api_client = YouTubeDataApiClient()
    super().__init__(api_client, parser, query_spec)

  def _generate_random_values(
    self,
    response_types: dict[str, Any],
  ) -> dict[str, Any]:
    return self.api_client._generate_random_values(response_types)
