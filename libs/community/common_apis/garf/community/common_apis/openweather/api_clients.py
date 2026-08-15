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

"""API client for OpenWeatherMap API."""

from __future__ import annotations

import logging

import requests
from garf.community.common_apis import exceptions
from garf.core import api_clients, query_editor

logger = logging.getLogger(__name__)

_DEFAULT_ENDPOINT = 'https://api.openweathermap.org/data/2.5'


class OpenWeatherApiClientError(exceptions.CommonApiError):
  """OpenWeather API client specific error."""


class OpenWeatherApiClient(api_clients.RestApiClient):
  """Client for interacting with OpenWeatherMap API.

  Wraps the garf REST client with OpenWeatherMap-specific behaviour:

  - The API key is stored on the client and injected as the ``appid`` query
    parameter on every request.  It never appears in query files or logs.
  - OpenWeather endpoints return a single JSON object rather than a list;
    the response is wrapped in a list so standard garf parsers work normally.
  - List responses (e.g. the ``/forecast`` endpoint returns ``{"list": [...]}``
    at the top level but some custom endpoints return raw arrays) are passed
    through unchanged.

  Args:
    api_key: OpenWeatherMap API key.
    endpoint: Base URL for the API.  Defaults to the v2.5 data endpoint.
      Must be a valid ``https://`` or ``http://`` URL.  Validated by the
      parent class SSRF protection layer.
    **kwargs: Forwarded to :class:`~garf.core.api_clients.RestApiClient`.
  """

  def __init__(
    self,
    api_key: str,
    endpoint: str = _DEFAULT_ENDPOINT,
    **kwargs: str,
  ) -> None:
    if not api_key:
      raise OpenWeatherApiClientError(
        'An OpenWeatherMap API key is required. '
        'Generate one at https://openweathermap.org/appid'
      )
    # Remove api_key from kwargs before passing to the parent so it is not
    # stored in self.query_args, which is visible on the object.
    kwargs.pop('api_key', None)
    super().__init__(endpoint=endpoint, **kwargs)
    self._api_key = api_key

  def get_response(
    self,
    request: query_editor.BaseQueryElements,
    **kwargs: str,
  ) -> api_clients.GarfApiResponse:
    """Fetches data from OpenWeatherMap and normalizes the response.

    Args:
      request: Parsed query elements.  ``resource_name`` becomes the path
        segment appended to the base endpoint (e.g. ``weather``,
        ``forecast``).  ``filters`` are forwarded as query parameters.
      **kwargs: Ignored (present for interface compatibility).

    Returns:
      :class:`~garf.core.api_clients.GarfApiResponse` whose ``results`` is
      always a list of dicts.

    Raises:
      OpenWeatherApiClientError: When the API returns a non-200 status.
    """
    url = f'{self.endpoint}/{request.resource_name}'
    params: dict[str, str] = {}
    for filter_statement in request.filters:
      key, value = filter_statement.split('=', 1)
      params[key.strip()] = value.strip()
    # Inject auth last so user filters cannot override it.
    params['appid'] = self._api_key

    response = requests.get(url, params=params)
    if response.status_code == self.OK:
      data = response.json()
      if not isinstance(data, (dict, list)):
        raise OpenWeatherApiClientError(
          f'Unexpected response format from OpenWeather API '
          f'(HTTP {response.status_code}): response is not a JSON object or array.'
        )
      results: list[dict] = data if isinstance(data, list) else [data]
      return api_clients.GarfApiResponse(results=results)
    # Deliberately omit response body from the exception message to avoid
    # leaking any reflected auth tokens or PII that the API might echo back.
    raise OpenWeatherApiClientError(
      f'OpenWeather API request failed with HTTP {response.status_code}. '
      f'Check your API key and query parameters.'
    )
