# Copyright 2024 Google LLC
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
"""Creates API client for YouTube Data API."""

import os
import warnings

from googleapiclient.discovery import build
from typing_extensions import override

from garf_core import api_clients, query_editor
from garf_youtube_data_api import exceptions


class YouTubeDataApiClientError(exceptions.GarfYouTubeDataApiError):
  """API client specific exception."""


class YouTubeDataApiClient(api_clients.BaseClient):
  """Handles fetching data form YouTube Data API."""

  def __init__(
    self,
    api_key: str = os.getenv('GARF_YOUTUBE_DATA_API_KEY'),
    api_version: str = 'v3',
    **kwargs: str,
  ) -> None:
    """Initializes YouTubeDataApiClient."""
    if not api_key and os.getenv('GOOGLE_API_KEY'):
      warnings.DeprecatingWarning(
        'You are using deprecated GOOGLE_API_KEY variable to create '
        'YouTubeDataApiClient. Use GARF_YOUTUBE_DATA_API_KEY variable instead'
      )
      api_key = os.getenv('GOOGLE_API_KEY')
    if not api_key:
      raise YouTubeDataApiClientError(
        'api_key is not found. Either pass to YouTubeDataApiClient as api_key '
        'parameter or expose as GARF_YOUTUBE_DATA_API_KEY ENV variable'
      )
    self.api_key = api_key
    self.api_version = api_version
    self.api_key
    self.query_args = kwargs
    self._service = None

  @property
  def service(self):
    if self._service:
      return self._service
    return build('youtube', self.api_version, developerKey=self.api_key)

  @override
  def get_response(
    self, request: query_editor.BaseQueryElements, **kwargs: str
  ) -> api_clients.GarfApiResponse:
    fields = [field.split('.')[0] for field in request.fields]
    sub_service = getattr(self.service, request.resource_name)()
    part_str = ','.join(fields)
    result = self._list(sub_service, part=part_str, **kwargs)
    results = []
    results.extend(result.get('items'))
    while result.get('nextPageToken'):
      result = self._list(
        sub_service,
        part=part_str,
        next_page_token=result.get('nextPageToken'),
        **kwargs,
      )
      results.extend(result.get('items'))

    return api_clients.GarfApiResponse(results=results)

  def _list(
    self, service, part: str, next_page_token: str | None = None, **kwargs
  ) -> list:
    if next_page_token:
      return service.list(
        part=part, pageToken=next_page_token, **kwargs
      ).execute()
    return service.list(part=part, **kwargs).execute()
