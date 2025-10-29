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

"""Defines report fetcher for Bid Manager API."""

from garf_core import parsers, report_fetcher

from garf_bid_manager import BidManagerApiClient, query_editor


class BidManagerApiReportFetcher(report_fetcher.ApiReportFetcher):
  """Defines report fetcher."""

  def __init__(
    self,
    api_client: BidManagerApiClient | None = None,
    parser: parsers.DictParser = parsers.NumericConverterDictParser,
    query_spec: query_editor.BidManagerApiQuery = (
      query_editor.BidManagerApiQuery
    ),
    **kwargs: str,
  ) -> None:
    """Initializes BidManagerApiReportFetcher."""
    if not api_client:
      api_client = BidManagerApiClient(**kwargs)
    super().__init__(api_client, parser, query_spec, **kwargs)
