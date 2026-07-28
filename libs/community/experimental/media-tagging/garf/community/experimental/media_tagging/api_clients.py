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

"""API client to work with media tagging."""

import logging
import urllib.parse

import garf.executors
import requests
from garf.community.experimental.media_tagging import query_editor
from garf.core import api_clients
from opentelemetry import trace
from opentelemetry.trace.propagation.tracecontext import (
  TraceContextTextMapPropagator,
)

from media_tagging import MediaTaggingRequest, MediaTaggingService, repositories

tracer = trace.get_tracer(
  instrumenting_module_name='garf.community.experimental.media_tagging',
)


logger = logging.getLogger('media-tagger')
logger.setLevel(logging.WARNING)


class MediaTaggingApiClient(api_clients.RestApiClient):
  """Client to work with media tagger.

  MediaTaggingApiClient work work local and remote instances of MediaTagging.

  Attributes:
    endpoint: HTTP endpoint when media tagger is running.
    db_uri: Connection string to DB where media tagger stores tagging results.
  """

  def __init__(
    self,
    endpoint: str | None = None,
    db_uri: str | None = None,
    tagger_type: str = 'gemini',
    schema=None,
    custom_prompt=None,
    **kwargs: str,
  ):
    self.endpoint = endpoint
    self.db_uri = db_uri
    self.tagger_type = tagger_type
    self.schema = schema
    self.custom_prompt = custom_prompt
    self.kwargs = kwargs

  def get_response(
    self, request: query_editor.MediaTaggingApiQuery, **kwargs: str
  ) -> api_clients.GarfApiResponse:
    if schema := kwargs.get('tagging_options', {}).get('custom_schema'):
      kwargs['tagging_options'].update(query_editor.process_schema(schema))
    media_paths = kwargs.get('media_paths') or request.filters.get(
      'media_paths'
    )
    tagging_parameters = garf.executors.utils.merge_dicts(
      kwargs, request.filters
    )
    if custom_prompt := tagging_parameters.get('tagging_options', {}).get(
      'custom_prompt'
    ):
      tagging_parameters['tagging_options'].update(
        {
          'custom_prompt': custom_prompt[0]
          if isinstance(custom_prompt, list)
          else custom_prompt
        }
      )

    if not media_paths:
      logger.warning('No media provided, generating placeholders')
      service = MediaTaggingService()
      tagging_parameters['tagger_type'] = 'fake'
      tagging_parameters['media_paths'] = ['placeholder']
      tagging_request = MediaTaggingRequest(**tagging_parameters)
      if request.resource_name == 'description':
        response = service.describe_media(tagging_request)
      else:
        response = service.tag_media(tagging_request)
      results = [result.model_dump() for result in response.results]
      return api_clients.GarfApiResponse(
        results=[], results_placeholder=results
      )
    if not isinstance(media_paths, list):
      media_paths = [media_paths]

    tagging_parameters['media_paths'] = media_paths
    tagging_request = MediaTaggingRequest(**tagging_parameters)
    with tracer.start_as_current_span('request') as span:
      span.set_attribute(
        'media_tagger.num_media_to_process', len(tagging_request.media_paths)
      )
      span.set_attribute('media_tagger.media_type', tagging_request.media_type)
      span.set_attribute(
        'media_tagger.tagger_type', tagging_request.tagger_type
      )
      span.set_attribute(
        'media_tagger.backend', 'remote' if self.endpoint else 'local'
      )
    if self.endpoint:
      headers = {}
      TraceContextTextMapPropagator().inject(headers)
      resource = 'describe' if request.resource_name == 'description' else 'tag'
      url = urllib.parse.urljoin(self.endpoint, f'/{resource}')
      response = requests.post(
        url=url,
        json=tagging_request.model_dump(exclude_none=True),
        headers=headers,
      )
      response.raise_for_status()
      results = response.json().get('results')
      return api_clients.GarfApiResponse(results=results, full_results=results)
    service = MediaTaggingService(
      repositories.SqlAlchemyTaggingResultsRepository(self.db_uri)
    )
    if request.resource_name == 'description':
      response = service.describe_media(tagging_request)
    else:
      response = service.tag_media(tagging_request)
    results = [result.model_dump() for result in response.results]
    return api_clients.GarfApiResponse(results=results)
