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
import json
import logging
import os
import pathlib
from typing import Literal

import smart_open
import tenacity
from garf.community.google.bid_manager import exceptions, query_editor
from garf.core import api_clients
from google.oauth2 import service_account
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from typing_extensions import override

_API_URL = 'https://doubleclickbidmanager.googleapis.com/'
_DEFAULT_API_SCOPES = ['https://www.googleapis.com/auth/doubleclickbidmanager']

_SERVICE_ACCOUNT_CREDENTIALS_FILE = str(pathlib.Path.home() / 'dbm.json')
_QUERY_CACHE_ENV = 'GARF_BID_MANAGER_QUERY_CACHE_DIR'
_DEFAULT_QUERY_CACHE_DIR = pathlib.Path.home() / '.garf/bid_manager'


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
    query_cache_dir: str | pathlib.Path | None = None,
    **kwargs: str,
  ) -> None:
    """Initializes BidManagerApiClient."""
    self.api_version = api_version
    self.credentials_file = credentials_file
    self.auth_mode = auth_mode
    self.kwargs = kwargs
    self._client = None
    self._credentials = None
    cache_dir = query_cache_dir or os.getenv(_QUERY_CACHE_ENV)
    self.query_cache_dir = (
      pathlib.Path(cache_dir) if cache_dir else _DEFAULT_QUERY_CACHE_DIR
    )

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
    query_hash = request.hash
    query_id = None
    report_id = None
    status = None

    if cached_ids := self._load_cached_query_reference(query_hash):
      cached_query_id, cached_report_id = cached_ids
      logging.info(
        'Attempting to reuse DV360 report %s for query hash %s.',
        cached_report_id,
        query_hash,
      )
      try:
        status = self._get_report_status(cached_query_id, cached_report_id)
        query_id, report_id = cached_query_id, cached_report_id
      except Exception as exc:  # pylint: disable=broad-except
        logging.warning(
          'Unable to reuse DV360 report %s (hash %s), regenerating. Reason: %s',
          cached_report_id,
          query_hash,
          exc,
        )
        status = None

    if status is None:
      query_id, report_id = self._run_query(request)
      self._save_cached_query_reference(query_hash, query_id, report_id)
      status = self._get_report_status(query_id, report_id)

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

  def _run_query(
    self, request: query_editor.BidManagerApiQuery
  ) -> tuple[str, str]:
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
      'Query %s is running, report %s has been created and is currently '
      'being generated.',
      query_id,
      report_id,
    )
    return query_id, report_id

  def _get_report_status(self, query_id: str, report_id: str):
    get_request = (
      self.client.queries()
      .reports()
      .get(
        queryId=query_id,
        reportId=report_id,
      )
    )
    return _check_if_report_is_done(get_request)

  def _load_cached_query_reference(
    self, query_hash: str
  ) -> tuple[str, str] | None:
    cache_path = self.query_cache_dir / f'{query_hash}.txt'
    if not cache_path.is_file():
      return None
    try:
      with open(cache_path, 'r', encoding='utf-8') as cache_file:
        data = json.load(cache_file)
      return data['query_id'], data['report_id']
    except (OSError, ValueError, KeyError) as exc:
      logging.warning(
        'Failed to load DV360 cache file %s, ignoring. Reason: %s',
        cache_path,
        exc,
      )
      return None

  def _save_cached_query_reference(
    self, query_hash: str, query_id: str, report_id: str
  ) -> None:
    self.query_cache_dir.mkdir(parents=True, exist_ok=True)
    cache_path = self.query_cache_dir / f'{query_hash}.txt'
    with open(cache_path, 'w', encoding='utf-8') as cache_file:
      json.dump({'query_id': query_id, 'report_id': report_id}, cache_file)


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
  stop=tenacity.stop_after_attempt(100), wait=tenacity.wait_exponential(max=120)
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
