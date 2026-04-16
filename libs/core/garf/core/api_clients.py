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
"""Module for defining client to interact with API."""

from __future__ import annotations

import abc
import contextlib
import csv
import ipaddress
import json
import os
from collections.abc import Sequence
from typing import Any, Union
from urllib.parse import urlparse

import pydantic
import requests
import smart_open
from garf.core import exceptions, query_editor
from garf.core.telemetry import tracer
from opentelemetry import metrics, trace
from typing_extensions import TypeAlias, override

ApiRowElement: TypeAlias = Union[int, float, str, bool, list, dict, None]
ApiResponseRow: TypeAlias = dict[str, ApiRowElement]

meter = metrics.get_meter('garf.core')

api_counter = meter.create_counter(
  'garf_api_call_total',
  unit='1',
  description='Counts number of requests to API',
)


class GarfApiResponse(pydantic.BaseModel):
  """Base class for specifying response."""

  results: list[ApiResponseRow | Any]
  results_placeholder: list[ApiResponseRow | Any] | None = pydantic.Field(
    default_factory=list
  )

  def model_post_init(self, __context__) -> None:
    if self.results_placeholder is None:
      self.results_placeholder = []

  def __bool__(self) -> bool:
    return bool(self.results)


class GarfApiError(exceptions.GarfError):
  """API specific exception."""


# Blocked IP ranges for SSRF protection.
# Defined at module level so it is built once and reused on every call.
_SSRF_BLOCKED_RANGES: list[ipaddress.IPv4Network | ipaddress.IPv6Network] = [
  ipaddress.ip_network(n)
  for n in (
    '169.254.0.0/16',  # link-local — AWS IMDS & GCE metadata endpoint
    '127.0.0.0/8',     # IPv4 loopback
    '10.0.0.0/8',      # RFC-1918 private
    '172.16.0.0/12',   # RFC-1918 private
    '192.168.0.0/16',  # RFC-1918 private
    '::1/128',         # IPv6 loopback
    'fe80::/10',       # IPv6 link-local
  )
]


def _validate_endpoint_url(url: str) -> None:
  """Validates an endpoint URL to prevent SSRF attacks.

  Ensures the URL uses an allowed scheme (http or https) and does not
  resolve to a loopback, link-local, or RFC-1918 IP address that could
  be used to reach cloud metadata services or internal infrastructure.

  Args:
    url: The endpoint URL to validate.

  Raises:
    GarfApiError: If the URL scheme is not http/https, or if the host is
      a bare IP address that falls within a blocked range.
  """
  try:
    parsed = urlparse(url)
  except Exception as e:
    raise GarfApiError(f'Invalid endpoint URL: {url!r}') from e
  if parsed.scheme not in ('http', 'https'):
    raise GarfApiError(
      f'Endpoint must use http or https scheme, got: {parsed.scheme!r}'
    )
  if parsed.hostname:
    try:
      addr = ipaddress.ip_address(parsed.hostname)
      for net in _SSRF_BLOCKED_RANGES:
        if addr in net:
          raise GarfApiError(
            f'Endpoint resolves to a blocked address range: {addr}'
          )
    except ValueError:
      pass  # hostname string rather than a bare IP — allowed through


class BaseClient(abc.ABC):
  """Base API client class."""

  @tracer.start_as_current_span('call_api')
  def call_api(
    self, request: query_editor.BaseQueryElements, **kwargs: str
  ) -> GarfApiResponse:
    """Method for getting response."""
    span = trace.get_current_span()
    response = self.get_response(request, **kwargs)
    span.set_attribute('num_rows_api_response', len(response.results))
    api_counter.add(1, {'api.client.class': self.__class__.__name__})
    return response

  @abc.abstractmethod
  def get_response(
    self, request: query_editor.BaseQueryElements, **kwargs: str
  ) -> GarfApiResponse:
    """Method for getting response."""

  def get_types(
    self, request: query_editor.BaseQueryElements | None = None, **kwargs: str
  ) -> dict[str, Any]:
    """Method for getting response."""
    raise NotImplementedError


class RestApiClient(BaseClient):
  """Specifies REST client."""

  OK = 200

  def __init__(self, endpoint: str, **kwargs: str) -> None:
    """Initializes RestApiClient."""
    _validate_endpoint_url(endpoint)
    self.endpoint = endpoint
    self.query_args = kwargs

  @override
  def get_response(
    self, request: query_editor.BaseQueryElements, **kwargs: str
  ) -> GarfApiResponse:
    url = f'{self.endpoint}/{request.resource_name}'
    params = {}
    for param in request.filters:
      key, value = param.split('=')
      params[key.strip()] = value.strip()
    response = requests.get(url, params=params, headers=kwargs)
    if response.status_code == self.OK:
      results = response.json()
      if not isinstance(results, list):
        results = [results]
      return GarfApiResponse(results=results)
    raise GarfApiError('Failed to get data from API, reason: ', response.text)


class FakeApiClient(BaseClient):
  """Fake class for specifying API client."""

  def __init__(
    self,
    results: Sequence[dict[str, Any]],
    results_placeholder: Sequence[dict[str, Any]] | None = None,
    **kwargs: str,
  ) -> None:
    """Initializes FakeApiClient."""
    self.results = list(results)
    self.results_placeholder = (
      self.results if not results_placeholder else list(results_placeholder)
    )
    self.kwargs = kwargs

  @override
  def get_response(
    self, request: query_editor.BaseQueryElements, **kwargs: str
  ) -> GarfApiResponse:
    del request
    return GarfApiResponse(
      results=self.results, results_placeholder=self.results_placeholder
    )

  @override
  def get_types(self, request=None, nested=None):
    results = {}
    for key, value in (nested or self.results[0]).items():
      if isinstance(value, dict):
        results[key] = self.get_types(nested=value)
      else:
        results[key] = type(value)
    return results

  @classmethod
  def from_file(cls, file_location: str | os.PathLike[str]) -> FakeApiClient:
    """Initializes FakeApiClient from json or csv files.

    Args:
      file_location: Path of file with data.

    Returns:
      Initialized client.

    Raises:
      GarfApiError: When file with unsupported extension is provided.
    """
    if str(file_location).endswith('.json'):
      return FakeApiClient.from_json(file_location)
    if str(file_location).endswith('.csv'):
      return FakeApiClient.from_csv(file_location)
    raise GarfApiError(
      'Unsupported file extension, only csv and json are supported.'
    )

  @classmethod
  def from_json(cls, file_location: str | os.PathLike[str]) -> FakeApiClient:
    """Initializes FakeApiClient from json file.

    Args:
      file_location: Path of file with data.

    Returns:
      Initialized client.

    Raises:
      GarfApiError: When file with data not found.
    """
    try:
      with smart_open.open(file_location, 'r', encoding='utf-8') as f:
        data = json.load(f)
        return FakeApiClient(data)
    except FileNotFoundError as e:
      raise GarfApiError(f'Failed to open {file_location}') from e

  @classmethod
  def from_csv(cls, file_location: str | os.PathLike[str]) -> FakeApiClient:
    """Initializes FakeApiClient from csv file.

    Args:
      file_location: Path of file with data.

    Returns:
      Initialized client.

    Raises:
      GarfApiError: When file with data not found.
    """
    try:
      with smart_open.open(file_location, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        data = []
        for row in reader:
          data.append(
            {key: _field_converter(value) for key, value in row.items()}
          )
        return FakeApiClient(data)
    except (AttributeError, FileNotFoundError) as e:
      raise GarfApiError(f'Failed to open {file_location}') from e


def _field_converter(field: str):
  if isinstance(field, str) and (lower_field := field.lower()) in (
    'true',
    'false',
  ):
    return lower_field == 'true'
  with contextlib.suppress(ValueError):
    return int(field)
  with contextlib.suppress(ValueError):
    return float(field)
  return field