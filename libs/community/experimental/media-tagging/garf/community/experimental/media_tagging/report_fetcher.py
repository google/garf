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

"""Defines report fetcher for Media Tagging API."""

from garf.community.experimental.media_tagging import (
  api_clients,
  query_editor,
  version,
)
from garf.core import parsers, report_fetcher


class MediaTaggingApiReportFetcher(report_fetcher.ApiReportFetcher):
  """Defines report fetcher."""

  version = version.__version__

  def __init__(
    self,
    api_client: api_clients.MediaTaggingApiClient | None = None,
    parser: parsers.DictParser = parsers.DictParser,
    query_spec: query_editor.MediaTaggingApiQuery = (
      query_editor.MediaTaggingApiQuery
    ),
    **kwargs: str,
  ) -> None:
    """Initializes MediaTaggingApiReportFetcher."""
    if not api_client:
      api_client = api_clients.MediaTaggingApiClient(**kwargs)
    super().__init__(api_client, parser, query_spec, **kwargs)
