# Copyright 2024 Google LLf
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
"""Module for getting data from Ads API based on a query.

AdsReportFetcher performs fetching data from Ads API, parsing it
  and returning GarfReport.
"""
# pylint: disable=C0330, g-bad-import-order, g-multiple-import

from __future__ import annotations

import logging
from typing import Any

from garf_core import (
  api_clients,
  parsers,
  query_editor,
  report,
)

logger = logging.getLogger(__name__)


class ApiReportFetcher:
  """Class responsible for getting data from Ads API.

  Attributes:
      api_client: a client used for connecting to Ads API.
  """

  def __init__(
    self,
    api_client: api_clients.BaseApiClient,
    parser: parsers.BaseParser = parsers.ListParser,
  ) -> None:
    """Instantiates AdsReportFetcher based on provided api client.

    Args:
      api_client: Instantiated GoogleAdsClient or GoogleAdsApiClient.
      parser: Parser.
    """
    self.api_client = api_client
    self.parser = parser()

  async def afetch(
    self,
    query_specification: str | query_editor.QueryElements,
    args: dict[str, Any] | None = None,
    **kwargs: str,
  ) -> report.GarfReport:
    """Asynchronously fetches data from Ads API based on query_specification.

    Args:
        query_specification: Query text that will be passed to Ads API
            alongside column_names, customizers and virtual columns.
        args: Arguments that need to be passed to the query.

    Returns:
        GarfReport with results of query execution.
    """
    return self.fetch(query_specification, args, **kwargs)

  def fetch(
    self,
    query_specification: str | query_editor.QuerySpecification,
    args: dict[str, Any] | None = None,
    **kwargs: str,
  ) -> report.GarfReport:
    """Fetches data from Ads API based on query_specification.

    Args:
        query_specification: Query text that will be passed to Ads API
            alongside column_names, customizers and virtual columns.
        args: Arguments that need to be passed to the query.

    Returns:
        GarfReport with results of query execution.

    Raises:
        GarfExecutorException:
            When customer_ids are not provided or Ads API returned error.
    """
    if not isinstance(query_specification, query_editor.QuerySpecification):
      query_specification = query_editor.QuerySpecification(
        text=str(query_specification),
        args=args,
      )
    query = query_specification.generate()
    response = self.api_client.get_response(query, **kwargs)
    parsed_response = self.parser.parse_response(response, query)
    return report.GarfReport(
      results=parsed_response, column_names=query.column_names
    )
