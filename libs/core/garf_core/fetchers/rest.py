# Copyright 2025 Google LLf
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

# pylint: disable=C0330, g-bad-import-order, g-multiple-import

"""Module for getting data from Rest APIs based on a query."""

from __future__ import annotations

import logging

from garf_core import (
  api_clients,
  parsers,
  query_editor,
  report_fetcher,
)

logger = logging.getLogger(__name__)


class RestApiReportFetcher(report_fetcher.ApiReportFetcher):
  """Fetches data from an REST API endpoint.

  Attributes:
    api_client: Initialized RestApiClient.
    parser: Type of parser to convert API response.
  """

  def __init__(
    self,
    api_client: api_clients.RestApiClient | None = None,
    parser: parsers.BaseParser = parsers.DictParser,
    query_specification_builder: query_editor.QuerySpecification = (
      query_editor.QuerySpecification
    ),
    endpoint: str | None = None,
    **kwargs: str,
  ) -> None:
    """Instantiates RestApiReportFetcher.

    Args:
      endpoint: URL of API endpoint.
      parser: Type of parser to convert API response.
      query_specification_builder: Class to perform query parsing.
    """
    if not api_client and not endpoint:
      raise report_fetcher.ApiReportFetcherError(
        'Missing api_client or endpoint for the fetcher.'
      )
    if not api_client:
      api_client = api_clients.RestApiClient(endpoint)
    super().__init__(api_client, parser, query_specification_builder, **kwargs)

  @classmethod
  def from_endpoint(cls, endpoint: str) -> RestApiReportFetcher:
    """Initializes RestApiReportFetcher: from an API endpoint."""
    return RestApiReportFetcher(
      api_client=api_clients.RestApiClient(endpoint=endpoint)
    )
