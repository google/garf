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

import csv
import io
import logging
import os
import pathlib
from typing import Literal

import smart_open
import tenacity
from garf_core import api_clients
from google.oauth2 import service_account
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from typing_extensions import override

from garf_bid_manager import exceptions, query_editor

_API_URL = 'https://doubleclickbidmanager.googleapis.com/'
_DEFAULT_API_SCOPES = ['https://www.googleapis.com/auth/doubleclickbidmanager']

_SERVICE_ACCOUNT_CREDENTIALS_FILE = str(pathlib.Path.home() / 'dbm.json')


class BidManagerApiClientError(exceptions.BidManagerApiError):
  """Bid Manager API client specific error."""


class BidManagerApiClient(api_clients.BaseClient):
  """Responsible for connecting to Bid Manager API."""

  def __init__(
    self,
    api_version: str = 'v2',
    credentials_file: str | pathlib.Path = os.getenv(
      'GARF_BID_MANAGER_CREDENTIALS_FILE', _SERVICE_ACCOUNT_CREDENTIALS_FILE
    ),
    auth_mode: Literal['oauth', 'service_account'] = 'oauth',
    **kwargs: str,
  ) -> None:
    """Initializes BidManagerApiClient."""
    self.api_version = api_version
    self.credentials_file = credentials_file
    self.auth_mode = auth_mode
    self.kwargs = kwargs
    self._client = None
    self._credentials = None

  @property
  def credentials(self):
    if not self._credentials:
      self._credentials = (
        self._get_oauth_credentials()
        if self.auth_mode == 'oauth'
        else self._get_service_account_credentials()
      )
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
    self, request: query_editor.BidManagerApiQuery, **kwargs: str
  ) -> api_clients.GarfApiResponse:
    query = _build_request(request)
    query_response = self.client.queries().create(body=query).execute()
    report_response = (
      self.client.queries()
      .run(queryId=query_response['queryId'], synchronous=False)
      .execute()
    )
    query_id = report_response['key']['queryId']
    report_id = report_response['key']['reportId']
    logging.info(
      'Query %s is running, report %s has been created and is '
      'currently being generated.',
      query_id,
      report_id,
    )

    get_request = (
      self.client.queries()
      .reports()
      .get(
        queryId=report_response['key']['queryId'],
        reportId=report_response['key']['reportId'],
      )
    )

    status = _check_if_report_is_done(get_request)

    logging.info(
      'Report %s generated successfully. Now downloading.', report_id
    )
    with smart_open.open(
      status['metadata']['googleCloudStoragePath'], 'r', encoding='utf-8'
    ) as f:
      data = f.readlines()
    results = _process_api_response(data[1:], request.fields)
    return api_clients.GarfApiResponse(results=results)

  def _get_service_account_credentials(self):
    if pathlib.Path(self.credentials_file).is_file():
      return service_account.Credentials.from_service_account_file(
        self.credentials_file, scopes=_DEFAULT_API_SCOPES
      )
    raise BidManagerApiClientError(
      'A service account key file could not be found at '
      f'{self.credentials_file}.'
    )

  def _get_oauth_credentials(self):
    if pathlib.Path(self.credentials_file).is_file():
      return InstalledAppFlow.from_client_secrets_file(
        self.credentials_file, _DEFAULT_API_SCOPES
      ).run_local_server(port=8088)
    raise BidManagerApiClientError(
      f'Credentials file could not be found at {self.credentials_file}.'
    )


def _build_request(request: query_editor.BidManagerApiQuery):
  """Builds Bid Manager API query object from BidManagerApiQuery."""
  query = {
    'metadata': {
      'title': request.title or 'garf',
      'format': 'CSV',
      'dataRange': {},
    },
    'params': {
      'type': request.resource_name,
    },
    'schedule': {'frequency': 'ONE_TIME'},
  }
  metrics = []
  group_bys = []
  for field in request.fields:
    if field.startswith('METRIC'):
      metrics.append(field)
    elif field.startswith('FILTER'):
      group_bys.append(field)
  filters = []
  for field in request.filters:
    name, operator, *value = field.split()
    if name.startswith('dataRange'):
      _, *date_identifier = name.split('.')
      if not date_identifier:
        query['metadata']['dataRange'] = {'range': value[0]}
      else:
        query['metadata']['dataRange']['range'] = 'CUSTOM_DATES'
        year, month, day = value[0].split('-')
        query['metadata']['dataRange'][date_identifier[0]] = {
          'day': int(day),
          'month': int(month),
          'year': int(year),
        }
    else:
      filters.append({'type': name, 'value': ' '.join(value)})
  query['params']['groupBys'] = group_bys
  query['params']['filters'] = filters
  if metrics:
    query['params']['metrics'] = metrics
  return query


def _process_api_response(
  data: list[str], fields
) -> list[api_clients.ApiResponseRow]:
  results = []
  for row in data:
    if row := row.strip():
      f = io.StringIO(row)
      reader = csv.reader(f)
      elements = next(reader)
      if not elements[0]:
        break
      result = dict(zip(fields, elements))
      results.append(result)
    else:
      break
  return results


@tenacity.retry(
  stop=tenacity.stop_after_attempt(100), wait=tenacity.wait_exponential()
)
def _check_if_report_is_done(get_request) -> bool:
  status = get_request.execute()
  state = status.get('metadata').get('status').get('state')
  if state != 'DONE':
    logging.debug(
      'Report %s it not ready, retrying...', status['key']['reportId']
    )
    raise Exception
  return status
