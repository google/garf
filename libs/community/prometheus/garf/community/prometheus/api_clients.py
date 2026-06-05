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

"""Handles to Prometheus HTTP API querying."""

import requests
from garf.community.prometheus import exceptions, query_editor
from garf.core import api_clients


class PrometheusApiClientError(exceptions.PrometheusApiError):
  """Prometheus HTTP API specific error."""


class PrometheusApiClient(api_clients.RestApiClient):
  """Specifies client for interacting with Prometheus HTTP API."""

  def __init__(
    self, endpoint: str = 'http://localhost:9090', **kwargs: str
  ) -> None:
    super().__init__(endpoint=endpoint, **kwargs)

  def get_response(
    self,
    request: query_editor.PrometheusApiQuery,
    **kwargs: str,
  ) -> api_clients.GarfApiResponse:
    url = f'{self.endpoint}/api/v1/{request.resource_name}'
    headers = {k: v for k, v in kwargs.items() if not isinstance(v, bool)}
    response = requests.get(url, params=request.filters, headers=headers)
    if response.status_code == self.OK:
      results = response.json()
      if request.resource_name == 'query_range':
        results = results.get('data').get('result')
        final_results = []
        for r in results:
          labels = r.get('metric')
          for row in r.get('values'):
            values = dict(zip(['timestamp', 'value'], row))
            final_results.append({**values, **labels})

      if request.resource_name == 'query':
        results = results.get('data').get('result')
        final_results = []
        for row in results:
          values = dict(zip(['timestamp', 'value'], row.get('value')))
          labels = row.get('metric')
          final_results.append({**values, **labels})
      return api_clients.GarfApiResponse(results=final_results)
    raise PrometheusApiClientError(
      'Failed to get data from Prometheus HTTP API, reason: ', response.text
    )
