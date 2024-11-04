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

from googleapiclient.discovery import build
from typing_extensions import override

from garf_core import api_clients, query_editor


class YouTubeDataApiClient(api_clients.BaseClient):
  def __init__(self, api_key: str, api_version: str = 'v3') -> None:
    """Initializes YouTubeDataApiClient."""
    self.api_key = api_key
    self.api_version = api_version
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
    sub_service = getattr(self.service, request.resource_name)
    result = sub_service().list(part=','.join(fields), **kwargs).execute()
    return api_clients.GarfApiResponse(results=result.get('items'))
