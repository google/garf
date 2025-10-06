# Copyright 2025 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the 'License');
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an 'AS IS' BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Creates API client for Bid Manager API."""

import os
import pathlib

import smart_open
from garf_core import api_clients, query_editor
from google.oauth2 import service_account
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from typing_extensions import override

from garf_bid_manager import exceptions

_API_URL = 'https://doubleclickbidmanager.googleapis.com/'
_DEFAULT_API_SCOPES = ['https://www.googleapis.com/auth/doubleclickbidmanager']

_SERVICE_ACCOUNT_CREDENTIALS_FILE = (
  str(pathlib.Path.home()) + '/configs/dbm.json'
)


class BidManagerApiClientError(exceptions.BidManagerApiError):
  """API client specific error."""


class BidManagerApiClient(api_clients.BaseClient):
  def __init__(self, api_version: str = 'v2') -> None:
    """Initializes BidManagerApiClient."""
    self.api_version = api_version
    self._client = None
    self._credentials = None

  @property
  def credentials(self):
    if not self._credentials:
      self._credentials = self.get_credentials()
    return self._credentials

  @property
  def client(self):
    if self._client:
      return self._client
    return build(
      'doubleclickbidmanager',
      self.api_version,
      discoveryServiceUrl=(
        f'{_API_URL}/$discovery/rest?version={self.api_version}'
      ),
      credentials=self.credentials,
    )

  @override
  def get_response(
    self, request: query_editor.BaseQueryElements, **kwargs: str
  ) -> api_clients.GarfApiResponse:
    filters = {'type': 'FILTER_ADVERTISER', 'value': ''}
    query_obj = {
      'metadata': {
        'title': 'test',
        'dataRange': {'range': 'LAST_7_DAYS'},
        'format': 'CSV',
      },
      'params': {
        'type': 'STANDARD',
        'groupBys': [
          'FILTER_ADVERTISER_NAME',
          'FILTER_ADVERTISER',
          'FILTER_ADVERTISER_CURRENCY',
          'FILTER_INSERTION_ORDER_NAME',
          'FILTER_INSERTION_ORDER',
          'FILTER_LINE_ITEM_NAME',
          'FILTER_LINE_ITEM',
        ],
        'filters': filters,
        'metrics': [
          'METRIC_IMPRESSIONS',
          'METRIC_BILLABLE_IMPRESSIONS',
          'METRIC_CLICKS',
          'METRIC_CTR',
          'METRIC_TOTAL_CONVERSIONS',
          'METRIC_LAST_CLICKS',
          'METRIC_LAST_IMPRESSIONS',
          'METRIC_REVENUE_ADVERTISER',
          'METRIC_MEDIA_COST_ADVERTISER',
        ],
      },
      'schedule': {'frequency': 'ONE_TIME'},
    }
    query_response = self.client.queries().create(body=query_obj).execute()
    report_response = (
      self.client.queries()
      .run(queryId=query_response['queryId'], synchronous=False)
      .execute()
    )
    query_id = report_response['key']['queryId']
    report_id = report_response['key']['reportId']
    print(
      f'Query {query_id} is running, report '
      f'{report_id} has been created and is '
      'currently being generated.'
    )

    # Configure the queries.reports.get request.
    get_request = (
      self.client.queries()
      .reports()
      .get(
        queryId=report_response['key']['queryId'],
        reportId=report_response['key']['reportId'],
      )
    )

    status = get_request.execute()
    state = status.get('metadata').get('status').get('state')

    print(f'Report {report_id} generated successfully. Now downloading.')
    with smart_open.open(
      status['metadata']['googleCloudStoragePath'], 'r', encoding='utf-8'
    ) as f:
      data = f.readlines()
    columns = data[0].strip().split(',')
    results = []
    for row in data[1:]:
      result = dict(zip(columns, row.strip().split(',')))
      results.append(result)
    return api_clients.GarfApiResponse(results=results)

  def get_service_account_credentials(self):
    """Steps through Service Account OAuth 2.0 flow to retrieve credentials."""
    service_account_credentials_file = _SERVICE_ACCOUNT_CREDENTIALS_FILE

    if os.path.isfile(service_account_credentials_file):
      return service_account.Credentials.from_service_account_file(
        service_account_credentials_file, scopes=_DEFAULT_API_SCOPES
      )
    raise BidManagerApiClientError(
      'A service account key file could not be found at '
      f'{service_account_credentials_file}.'
    )

  def get_credentials(self):
    """Steps through installed app OAuth 2.0 flow to retrieve credentials."""
    credentials_file = _SERVICE_ACCOUNT_CREDENTIALS_FILE

    # Asks for path to credentials file is not found in default location.
    if os.path.isfile(credentials_file):
      return InstalledAppFlow.from_client_secrets_file(
        credentials_file, _DEFAULT_API_SCOPES
      ).run_local_server(port=8088)
    raise BidManagerApiClientError(
      f'A service account key file could not be found at {credentials_file}.'
    )
