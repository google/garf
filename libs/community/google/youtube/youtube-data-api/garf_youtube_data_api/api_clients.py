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
"""Creates API client for YouTube Data API."""

import datetime
import functools
import logging
import operator
import os
import warnings
from typing import Any

import dateutil
import pydantic
from garf_core import api_clients, query_editor
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from opentelemetry import trace
from typing_extensions import override

from garf_youtube_data_api import exceptions, telemetry

logging.getLogger('googleapiclient.discovery_cache').setLevel(logging.ERROR)


class YouTubeDataApiClientError(exceptions.GarfYouTubeDataApiError):
  """API client specific exception."""


class YouTubeDataApiClient(api_clients.BaseClient):
  """Handles fetching data form YouTube Data API."""

  def __init__(
    self,
    api_key: str = os.getenv('GARF_YOUTUBE_DATA_API_KEY'),
    api_version: str = 'v3',
    **kwargs: str,
  ) -> None:
    """Initializes YouTubeDataApiClient."""
    if not api_key and os.getenv('GOOGLE_API_KEY'):
      warnings.warn(
        'You are using deprecated GOOGLE_API_KEY variable to create '
        'YouTubeDataApiClient. Use GARF_YOUTUBE_DATA_API_KEY variable instead',
        FutureWarning,
        stacklevel=2,
      )
      api_key = os.getenv('GOOGLE_API_KEY')
    if not api_key:
      raise YouTubeDataApiClientError(
        'api_key is not found. Either pass to YouTubeDataApiClient as api_key '
        'parameter or expose as GARF_YOUTUBE_DATA_API_KEY ENV variable'
      )
    self.api_key = api_key
    self.api_version = api_version
    self.api_key
    self.query_args = kwargs
    self._service = None

  @property
  def service(self):
    if self._service:
      return self._service
    return build('youtube', self.api_version, developerKey=self.api_key)

  def get_types(self, request):
    fields = {field.split('.')[0] for field in request.fields}
    return self.infer_types('Video', fields)

  def infer_types(self, name, fields):
    results = {}
    ress = self.service._schema.schemas.get(name)
    props = ress.get('properties')
    for field in fields:
      if prop := props.get(field):
        if ref := prop.get('$ref'):
          results[field] = self.infer_types(ref, [field])
        else:
          results[field] = prop.get('type') or prop.get('type')
      else:
        results.update(
          {k: v.get('format') or v.get('type') for k, v in props.items()}
        )
    return results

  def _generate_random_values(
    self,
    response_types: dict[str, Any],
  ) -> dict[str, Any]:
    results = {}
    type_mapping = {
      'string': '',
      'int64': 1,
      'int32': 1,
      'uint64': 1,
      'uint32': 1,
      'double': 1.0,
      'boolean': True,
      'date-time': '1970-01-01',
      'google-datetime': '1970-01-01T00:00:00Z',
      'google-duration': '2H',
    }
    for key, value in response_types.items():
      if isinstance(value, dict):
        results[key] = self._generate_random_values(value)
      else:
        results[key] = type_mapping.get(value)
    return results

  @override
  @telemetry.tracer.start_as_current_span('youtube_data_api.get_response')
  def get_response(
    self, request: query_editor.BaseQueryElements, **kwargs: str
  ) -> api_clients.GarfApiResponse:
    span = trace.get_current_span()
    for k, v in kwargs.items():
      span.set_attribute(f'youtube_data_api.kwargs.{k}', v)
    fields = {field.split('.')[0] for field in request.fields}
    sub_service = getattr(self.service, request.resource_name)()
    part_str = ','.join(fields)

    result = self._list(sub_service, part=part_str, **kwargs)
    results = []
    if data := result.get('items'):
      results.extend(data)
    while result.get('nextPageToken'):
      result = self._list(
        sub_service,
        part=part_str,
        next_page_token=result.get('nextPageToken'),
        **kwargs,
      )
      if data := result.get('items'):
        results.extend(data)

    if not results:
      types = self.get_types(request)
      results_placeholder = [self._generate_random_values(types)]
    else:
      results_placeholder = None
    if filters := request.filters:
      span.set_attribute('youtube_data_api.filters', filters)
      filtered_results = []
      comparators = []
      for filter in filters:
        field, op, value = filter.split(' ')
        comparators.append(Comparator(field=field, operator=op, value=value))
      with telemetry.tracer.start_as_current_span(
        'youtube_data_api.apply_filters'
      ):
        for row in results:
          include_row = True
          for comparator in comparators:
            key = comparator.field.split('.')
            res = functools.reduce(operator.getitem, key, row)
            if isinstance(comparator.value, datetime.date):
              expr = f'res {comparator.operator} comp'
              include_row = eval(
                expr,
                {
                  'res': dateutil.parser.parse(res).date(),
                  'comp': comparator.value,
                },
              )
            else:
              include_row = eval(
                f'{res} {comparator.operator} {comparator.value}', globals()
              )
            if not include_row:
              break
          if include_row:
            filtered_results.append(row)
      return api_clients.GarfApiResponse(
        results=filtered_results, results_placeholder=results_placeholder
      )
    return api_clients.GarfApiResponse(
      results=results, results_placeholder=results_placeholder
    )

  def _list(
    self, service, part: str, next_page_token: str | None = None, **kwargs
  ) -> dict:
    try:
      if next_page_token:
        return service.list(
          part=part, pageToken=next_page_token, **kwargs
        ).execute()
      return service.list(part=part, **kwargs).execute()
    except HttpError:
      return {'items': None}


class Comparator(pydantic.BaseModel):
  field: str
  operator: str
  value: str | datetime.date

  def model_post_init(self, __context) -> None:
    if self.operator == '=':
      self.operator = '=='
    if self.field in ('snippet.publishedAt'):
      self.value = dateutil.parser.parse(self.value).date()
