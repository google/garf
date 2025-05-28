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
"""Creates API client for Merchant API."""

from google.shopping import merchant_reports_v1beta
from typing_extensions import override

from garf_core import api_clients, query_editor
from garf_merchant_api import exceptions


class MerchantApiError(exceptions.GarfMerchantApiError):
  """API specific error."""


class MerchantApiClient(api_clients.BaseClient):
  def __init__(
    self,
    **kwargs: str,
  ) -> None:
    """Initializes MerchantClient."""
    self.query_args = kwargs

  @override
  def get_response(
    self, request: query_editor.BaseQueryElements, **kwargs: str
  ) -> api_clients.GarfApiResponse:
    if not (account := kwargs.get('account')):
      raise MerchantApiError('Missing account parameter')
    client = merchant_reports_v1beta.ReportServiceClient()
    merchant_request = merchant_reports_v1beta.SearchRequest(
      parent=f'accounts/{account}',
      query=request.text,
    )
    response = client.search(request=merchant_request)
    results = []
    for page in response:
      for result in page.get('results'):
        results.append(result)
    return api_clients.GarfApiResponse(results=results)
