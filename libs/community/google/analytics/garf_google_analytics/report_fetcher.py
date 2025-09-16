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

"""Defines report fetcher for Google Analytics API."""

from garf_core import parsers, report_fetcher

from garf_google_analytics import GoogleAnalyticsApiClient, query_editor


class GoogleAnalyticsApiReportFetcher(report_fetcher.ApiReportFetcher):
  """Defines report fetcher."""

  def __init__(
    self,
    api_client: GoogleAnalyticsApiClient = GoogleAnalyticsApiClient(),
    parser: parsers.DictParser = parsers.NumericConverterDictParser,
    query_spec: query_editor.GoogleAnalyticsApiQuery = (
      query_editor.GoogleAnalyticsApiQuery
    ),
    **kwargs: str,
  ) -> None:
    """Initializes GoogleAnalyticsApiReportFetcher."""
    super().__init__(api_client, parser, query_spec, **kwargs)
