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
"""Creates API client for DV360 API."""

from google.shopping import dv360_reports_v1beta
from typing_extensions import override

from garf_core import api_clients, query_editor
from garf_dv360_api import exceptions


class DV360ApiError(exceptions.GarfDV360ApiError):
  """API specific error."""


class DV360ApiClient(api_clients.BaseClient):
  def __init__(
    self,
    api_version: str = 'v4',
    **kwargs: str,
  ) -> None:
    """Initializes DV360Client."""
    self.api_version = api_version
    self.query_args = kwargs

  @override
  def get_response(
    self, request: query_editor.BaseQueryElements, **kwargs: str
  ) -> api_clients.GarfApiResponse:
    if not (account := kwargs.get('account')):
      raise DV360ApiError('Missing account parameter')
    client = dv360_reports_v1beta.ReportServiceClient()
    dv360_request = dv360_reports_v1beta.SearchRequest(
      parent=f'accounts/{account}',
      query=request.text,
    )
    response = client.search(request=dv360_request)
    results = []
    for page in response:
      for rows in page.get('results'):
        for _, row in rows.items():
          results.append(row)
    return api_clients.GarfApiResponse(results=results)
