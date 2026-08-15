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

"""API client for CurrencyAPI (currencyapi.com)."""

from __future__ import annotations

import logging

import requests
from garf.community.common_apis import exceptions
from garf.core import api_clients, query_editor

logger = logging.getLogger(__name__)

_DEFAULT_ENDPOINT = 'https://api.currencyapi.com/v3'


class CurrencyApiClientError(exceptions.CommonApiError):
  """CurrencyAPI client specific error."""


class CurrencyApiClient(api_clients.RestApiClient):
  """Client for interacting with CurrencyAPI (currencyapi.com).

  Wraps the garf REST client with CurrencyAPI-specific behaviour:

  - The API key is stored on the client and injected as the ``apikey`` HTTP
    request header on every request.  It never appears in query files, URLs,
    or logs.
  - CurrencyAPI wraps all currency data under a ``data`` key whose values are
    objects keyed by currency code::

        {"meta": {...}, "data": {"USD": {"code": "USD", "value": 1.08}, ...}}

    This client flattens the ``data`` dict into a plain list of currency
    objects so garf queries can use ``SELECT code, value`` directly without
    needing customizers or knowledge of the response shape.
  - Top-level scalar metadata fields (e.g. ``last_updated_at`` from ``meta``)
    are merged into each row so they are available as selectable columns.
  - Empty or missing ``data`` fields are handled gracefully and return an
    empty result set rather than raising.

  Args:
    api_key: CurrencyAPI secret key.
    endpoint: Base URL for the API.  Defaults to the v3 endpoint.  Must be a
      valid ``https://`` or ``http://`` URL.
    **kwargs: Forwarded to :class:`~garf.core.api_clients.RestApiClient`.
  """

  def __init__(
    self,
    api_key: str,
    endpoint: str = _DEFAULT_ENDPOINT,
    **kwargs: str,
  ) -> None:
    if not api_key:
      raise CurrencyApiClientError(
        'A CurrencyAPI key is required. '
        'Generate one at https://currencyapi.com/docs'
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
    """Fetches exchange-rate data from CurrencyAPI and normalizes the response.

    Args:
      request: Parsed query elements.  ``resource_name`` maps to the API
        endpoint path (e.g. ``latest``, ``historical``).  ``filters`` are
        forwarded as query parameters.
      **kwargs: Ignored (present for interface compatibility).

    Returns:
      :class:`~garf.core.api_clients.GarfApiResponse` whose ``results`` is a
      flat list of currency dicts, one per currency code.

    Raises:
      CurrencyApiClientError: When the API returns a non-200 status or the
        response body cannot be parsed.
    """
    url = f'{self.endpoint}/{request.resource_name}'
    params: dict[str, str] = {}
    for filter_statement in request.filters:
      key, value = filter_statement.split('=', 1)
      params[key.strip()] = value.strip()
    # API key goes in a header, never in the URL.
    headers = {'apikey': self._api_key}

    response = requests.get(url, params=params, headers=headers)
    if response.status_code == self.OK:
      try:
        payload = response.json()
      except Exception as exc:
        raise CurrencyApiClientError(
          'CurrencyAPI returned a non-JSON response.'
        ) from exc

      if not isinstance(payload, dict):
        raise CurrencyApiClientError(
          'Unexpected response format from CurrencyAPI: '
          'expected a JSON object at the top level.'
        )

      data = payload.get('data')

      # Handle missing or empty data gracefully.
      if not data:
        logger.warning(
          'CurrencyAPI response contained no data for resource %r.',
          request.resource_name,
        )
        return api_clients.GarfApiResponse(results=[])

      if isinstance(data, dict):
        results: list[dict] = list(data.values())
      elif isinstance(data, list):
        results = data
      else:
        raise CurrencyApiClientError(
          'Unexpected format for "data" field in CurrencyAPI response: '
          f'expected a dict or list, got {type(data).__name__}.'
        )

      # Merge top-level scalar metadata fields into every row so they are
      # available as selectable columns (e.g. last_updated_at).
      meta_scalars: dict = {}
      for key, value in payload.items():
        if key == 'data':
          continue
        # Flatten one level of nested meta objects (e.g. {"meta": {"last_updated_at": ...}})
        if isinstance(value, dict):
          meta_scalars.update(value)
        else:
          meta_scalars[key] = value

      if meta_scalars:
        results = [{**meta_scalars, **row} for row in results]

      return api_clients.GarfApiResponse(results=results)

    # Omit response body from the exception to avoid leaking auth tokens or
    # PII that the API might reflect back in error payloads.
    raise CurrencyApiClientError(
      f'CurrencyAPI request failed with HTTP {response.status_code}. '
      f'Check your API key and query parameters.'
    )
