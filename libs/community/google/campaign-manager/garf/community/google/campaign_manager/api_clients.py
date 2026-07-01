# Copyright 2026 Google LLC
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
"""Creates API client for Campaign Manager 360 API."""

import contextlib
import csv
import io
import json
import logging
import os
import pathlib
import pickle
import socket
from typing import Literal

import tenacity
from garf.community.google.campaign_manager import exceptions, query_editor
from garf.core import api_clients
from google.auth.transport.requests import Request
from google.oauth2 import service_account
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from typing_extensions import override

_API_URL = 'https://dfareporting.googleapis.com/'
_DEFAULT_API_SCOPES = [
  'https://www.googleapis.com/auth/dfareporting',
]

_SERVICE_ACCOUNT_CREDENTIALS_FILE = str(pathlib.Path.home() / 'cm360.json')
_QUERY_CACHE_ENV = 'GARF_CAMPAIGN_MANAGER_360_QUERY_CACHE_DIR'
_DEFAULT_QUERY_CACHE_DIR = pathlib.Path.home() / '.garf/cm360'
_CREDENTIALS_PATH = pathlib.Path.home() / '.garf/cm360/token.pickle'


logger = logging.getLogger(__name__)


class CampaignManager360ApiClientError(exceptions.CampaignManager360ApiError):
  """Campaign Manager 360 API client specific error."""


class CampaignManager360ApiClient(api_clients.BaseClient):
  """Responsible for connecting to Campaign Manager 360 API."""

  def __init__(
    self,
    profile_id: str,
    api_version: str = 'v5',
    credentials_file: str | pathlib.Path = os.getenv(
      'GARF_CAMPAIGN_MANAGER_360_CREDENTIALS_FILE',
      _SERVICE_ACCOUNT_CREDENTIALS_FILE,
    ),
    auth_mode: Literal['oauth', 'service_account'] = 'oauth',
    query_cache_dir: str | pathlib.Path | None = None,
    **kwargs: str,
  ) -> None:
    """Initializes CampaignManager360ApiClient."""
    if not profile_id:
      raise CampaignManager360ApiClientError('Missing profile_id parameter')
    self.profile_id = profile_id
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
      try:
        self._credentials = _load_credentials()
      except CampaignManager360ApiClientError:
        self._credentials = (
          self._get_oauth_credentials()
          if self.auth_mode == 'oauth'
          else self._get_service_account_credentials()
        )
    _save_credentials(self._credentials)
    return self._credentials

  @property
  def client(self):
    if not self._client:
      self._client = build(
        'dfareporting',
        self.api_version,
        discoveryServiceUrl=(
          f'{_API_URL}/$discovery/rest?version={self.api_version}'
        ),
        credentials=self.credentials,
      )
    return self._client

  @override
  def get_response(
    self, request: query_editor.CampaignManager360ApiQuery, **kwargs: str
  ) -> api_clients.GarfApiResponse:
    query_hash = request.hash
    file_id = None
    report_id = None
    status = None

    if cached_ids := self._load_cached_query_reference(query_hash):
      cached_file_id, cached_report_id = cached_ids
      logger.info(
        'Attempting to reuse CM360 report %s for query hash %s.',
        cached_report_id,
        query_hash,
      )
      try:
        status = self._get_report_status(cached_file_id, cached_report_id)
        file_id, report_id = cached_file_id, cached_report_id
      except Exception as exc:  # pylint: disable=broad-except
        logger.warning(
          'Unable to reuse CM360 report %s (hash %s), regenerating. Reason: %s',
          cached_report_id,
          query_hash,
          exc,
        )
        status = None

    if status is None:
      file_id, report_id = self._run_query(request)
      self._save_cached_query_reference(query_hash, file_id, report_id)
      status = self._get_report_status(file_id, report_id)

    logger.info('Report %s generated successfully. Now downloading.', report_id)
    data = (
      self.client.files()
      .get_media(reportId=report_id, fileId=file_id)
      .execute()
    )
    results = _process_api_response(data, request.fields)
    if not results:
      raise CampaignManager360ApiClientError('No data found in response')
    return api_clients.GarfApiResponse(results=results)

  def _get_service_account_credentials(self):
    if pathlib.Path(self.credentials_file).is_file():
      return service_account.Credentials.from_service_account_file(
        self.credentials_file, scopes=_DEFAULT_API_SCOPES
      )
    raise CampaignManager360ApiClientError(
      'A service account key file could not be found at '
      f'{self.credentials_file}.'
    )

  def _get_oauth_credentials(self):
    if pathlib.Path(self.credentials_file).is_file():
      with contextlib.closing(
        socket.socket(socket.AF_INET, socket.SOCK_STREAM)
      ) as s:
        s.bind(('', 0))
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        free_port = s.getsockname()[1]
      return InstalledAppFlow.from_client_secrets_file(
        self.credentials_file, _DEFAULT_API_SCOPES
      ).run_local_server(port=free_port)
    raise CampaignManager360ApiClientError(
      f'Credentials file could not be found at {self.credentials_file}.'
    )

  def _run_query(
    self, request: query_editor.CampaignManager360ApiQuery
  ) -> tuple[str, str]:
    query = _build_request(request)
    report = (
      self.client.reports()
      .insert(profileId=self.profile_id, body=query)
      .execute()
    )
    report_id = report['id']
    report_response = (
      self.client.reports()
      .run(profileId=self.profile_id, reportId=report_id)
      .execute()
    )
    file_id = report_response['id']
    logger.info(
      'Query %s is running, report %s has been created and is currently '
      'being generated.',
      file_id,
      report_id,
    )
    return file_id, report_id

  def _get_report_status(self, file_id: str, report_id: str):
    get_request = self.client.files().get(
      reportId=report_id,
      fileId=file_id,
    )
    return _check_is_report_is_available(get_request)

  def _load_cached_query_reference(
    self, query_hash: str
  ) -> tuple[str, str] | None:
    cache_path = self.query_cache_dir / f'{query_hash}.txt'
    if not cache_path.is_file():
      return None
    try:
      with open(cache_path, 'r', encoding='utf-8') as cache_file:
        data = json.load(cache_file)
      return data['file_id'], data['report_id']
    except (OSError, ValueError, KeyError) as exc:
      logger.warning(
        'Failed to load CM360 cache file %s, ignoring. Reason: %s',
        cache_path,
        exc,
      )
      return None

  def _save_cached_query_reference(
    self, query_hash: str, file_id: str, report_id: str
  ) -> None:
    self.query_cache_dir.mkdir(parents=True, exist_ok=True)
    cache_path = self.query_cache_dir / f'{query_hash}.txt'
    with open(cache_path, 'w', encoding='utf-8') as cache_file:
      json.dump({'file_id': file_id, 'report_id': report_id}, cache_file)


def _build_request(request: query_editor.CampaignManager360ApiQuery):
  """Builds CM360 API query object from CampaignManager360ApiQuery."""
  criteria_mapping = {
    'standard': 'criteria',
    'reach': 'reachCriteria',
    'path_to_conversion': 'pathToConversionCriteria',
    'floodlight': 'floodlightCriteria',
    'cross_dimension_reach': 'crossDimensionReachCriteria',
  }
  criteria = criteria_mapping.get(request.resource_name.lower())
  query = {
    'name': request.title or 'garf',
    'type': request.resource_name.upper(),
    'fileName': request.title or 'garf',
    'format': 'CSV',
    criteria: {
      'dateRange': {},
    },
  }

  metrics = []
  dimensions = []
  for field in request.fields:
    if field.startswith('metric'):
      _, metric_name = field.split('.')
      metrics.append(metric_name)
    elif field.startswith('dimension'):
      _, dimension_name = field.split('.')
      dimensions.append({'name': dimension_name})
    else:
      dimensions.append({'name': field})

  additional_filters = {
    'dimensionFilters': [],
    'reportProperties': {},
    'customRichMediaEvents': {},
    'floodlightConfigId': {},
    'activities': {},
    'reachByFrequencyMetricNames': [],
    'activityFilters': [],
    'conversionDimensions': [],
    'perInteractionDimensions': [],
    'customFloodlightVariables': [],
  }
  for field in request.filters:
    name, operator, *value = field.split()
    filter_type, *identifier = name.split('.')
    if name.startswith('dateRange'):
      query[criteria]['dateRange'][identifier[0]] = value[0]
    elif name.startswith('dimension'):
      additional_filters['dimensionFilters'].append(
        {'dimensionName': identifier[0], 'value': value[0]}
      )
    elif name.startswith('customRichMediaEvents'):
      additional_filters['customRichMediaEvents'].append(
        {'dimensionName': identifier[0], 'value': value[0]}
      )
    elif name.startswith('reportProperties'):
      additional_filters['reportProperties'][identifier[0]] = value[0]
  if present_filters := {a: v for a, v in additional_filters.items() if v}:
    query[criteria].update(present_filters)
  query[criteria]['dimensions'] = dimensions
  query[criteria]['metricNames'] = metrics
  return query


def _process_api_response(
  data: bytes, fields
) -> list[api_clients.ApiResponseRow]:
  data = str(data).split('Report Fields')[1].split('Grand Total')[0]
  data = data.split('\\n')[2:]
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
def _check_is_report_is_available(get_request) -> bool:
  status = get_request.execute()
  state = status.get('status')
  if state != 'REPORT_AVAILABLE':
    logger.debug('Report %s it not ready, retrying...', status['reportId'])
    raise Exception
  return status


def _load_credentials():
  if not os.path.exists(_CREDENTIALS_PATH):
    raise CampaignManager360ApiClientError('Credentials file not found')
  with open(_CREDENTIALS_PATH, 'rb') as f:
    credentials = pickle.load(f)
    if (
      not credentials.valid
      and credentials.expired
      and credentials.refresh_token
    ):
      credentials.refresh(Request())
    return credentials
  raise CampaignManager360ApiClientError('Credentials file not found')


def _save_credentials(credentials) -> None:
  with open(_CREDENTIALS_PATH, 'wb') as f:
    pickle.dump(credentials, f)
