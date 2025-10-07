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

"""Defines report fetcher for Google Ads API."""

import garf_core

from garf_google_ads import GoogleAdsApiClient, builtins, parsers, query_editor


class GoogleAdsApiReportFetcher(garf_core.ApiReportFetcher):
  """Defines report fetcher."""

  def __init__(
    self,
    api_client: GoogleAdsApiClient | None = None,
    parser: garf_core.parsers.ProtoParser = parsers.GoogleAdsRowParser,
    query_spec: query_editor.GoogleAdsApiQuery = (
      query_editor.GoogleAdsApiQuery
    ),
    builtin_queries=builtins.BUILTIN_QUERIES,
    **kwargs: str,
  ) -> None:
    """Initializes GoogleAdsApiReportFetcher."""
    if not api_client:
      api_client = GoogleAdsApiClient(**kwargs)
    super().__init__(api_client, parser, query_spec, builtin_queries, **kwargs)
