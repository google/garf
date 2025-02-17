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
"""Creates API client for YouTube Reporting API."""

import os
from collections import defaultdict

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from typing_extensions import override

from garf_core import api_clients, query_editor


class YouTubeReportingApiClient(api_clients.BaseClient):
  """Responsible for for getting data from YouTube Reporting API."""

  def __init__(self, api_version: str = 'v2') -> None:
    """Initializes YouTubeReportingApiClient."""
    self.api_version = api_version
    self._credentials = None
    self._service = None

  @property
  def credentials(self) -> Credentials:
    """OAuth2.0 credentials to access API."""
    if self._credentials:
      return self._credentials
    return Credentials(
      None,
      refresh_token=os.getenv('YT_REFRESH_TOKEN'),
      token_uri='https://oauth2.googleapis.com/token',
      client_id=os.getenv('YT_CLIENT_ID'),
      client_secret=os.getenv('YT_CLIENT_SECRET'),
    )

  @property
  def service(self):
    """Services for accessing YouTube Analytics API."""
    if self._service:
      return self._service
    return build(
      'youtubeAnalytics', self.api_version, credentials=self.credentials
    )

  @override
  def get_response(
    self, request: query_editor.BaseQueryElements, **kwargs: str
  ) -> api_clients.GarfApiResponse:
    metrics = []
    dimensions = []
    filters = []
    for field in request.fields:
      if field.startswith('metrics'):
        metrics.append(field.replace('metrics.', ''))
      elif field.startswith('dimensions'):
        dimensions.append(field.replace('dimensions.', ''))
    for filter_statement in request.filters:
      if filter_statement.startswith('channel'):
        ids = filter_statement
      elif filter_statement.startswith('startDate'):
        start_date = filter_statement.split('=')
      elif filter_statement.startswith('endDate'):
        end_date = filter_statement.split('=')
      else:
        filters.append(filter_statement)
    result = (
      self.service.reports()
      .query(
        dimensions=','.join(dimensions),
        metrics=','.join(metrics),
        filters=';'.join(filters),
        ids=ids,
        startDate=start_date[1].strip(),
        endDate=end_date[1].strip(),
        alt='json',
      )
      .execute()
    )
    results = []
    for row in result.get('rows'):
      response_row: dict[str, dict[str, str]] = defaultdict(dict)
      for position, header in enumerate(result.get('columnHeaders')):
        header_name = header.get('name')
        if header.get('columnType') == 'DIMENSION':
          response_row['dimensions'].update({header_name: row[position]})
        elif header.get('columnType') == 'METRIC':
          response_row['metrics'].update({header_name: row[position]})
      results.append(response_row)
    return api_clients.GarfApiResponse(results=results)
