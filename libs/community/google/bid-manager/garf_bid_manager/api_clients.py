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
"""Creates API client for Bid Manager API."""

from garf_core import api_clients, query_editor
from googleapiclient.discovery import build
from typing_extensions import override


class BidManagerApiClient(api_clients.BaseClient):
  def __init__(self, api_version: str = 'v2') -> None:
    """Initializes BidManagerApiClient."""
    self.api_version = api_version
    self._client = None

  @property
  def client(self):
    if self._client:
      return self._client
    credentials = None
    return build(
      'doubleclickbidmanager',
      self.api_version,
      discoveryServiceUrl='',
      credentials=credentials,
    )

  @override
  def get_response(
    self, request: query_editor.BaseQueryElements, **kwargs: str
  ) -> api_clients.GarfApiResponse:
    return api_clients.GarfApiResponse(results=[])
