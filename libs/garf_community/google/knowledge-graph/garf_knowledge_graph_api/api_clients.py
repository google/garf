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
"""Creates API client for Knowledge Graph Search API."""

import os

import requests
from typing_extensions import override

from garf_core import api_clients, query_editor


class KnowledgeGraphApiClient(api_clients.BaseClient):
  def __init__(
    self,
    api_key: str = os.getenv('KG_API_KEY'),
    **kwargs: str,
  ) -> None:
    """Initializes KnowledgeGraphApiClient."""
    self.api_key = api_key
    self.query_args = kwargs

  @override
  def get_response(
    self, request: query_editor.BaseQueryElements, **kwargs: str
  ) -> api_clients.GarfApiResponse:
    service_url = 'https://kgsearch.googleapis.com/v1/entities:search'
    params = {
      request.resource_name: request.filters,
      'limit': 100,
      'key': self.api_key,
    }
    response = requests.get(service_url, params=params)
    results = []
    for result in response.json().get('itemListElement', []):
      tmp_result = result.get('result')
      tmp_result.update({'result_score': result.get('resultScore')})
      results.append(tmp_result)
    return api_clients.GarfApiResponse(results=results)
