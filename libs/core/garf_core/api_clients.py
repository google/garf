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
import json
import os
from collections.abc import Sequence
from typing import Any, Union

import pydantic
import requests
import smart_open
from opentelemetry import trace
from typing_extensions import TypeAlias, override

from garf_core import exceptions, query_editor
from garf_core.telemetry import tracer

ApiRowElement: TypeAlias = Union[int, float, str, bool, list, dict, None]
ApiResponseRow: TypeAlias = dict[str, ApiRowElement]


class GarfApiResponse(pydantic.BaseModel):
  """Base class for specifying response."""

  results: list[ApiResponseRow]

  def __bool__(self) -> bool:
    return bool(self.results)


class GarfApiError(exceptions.GarfError):
  """API specific exception."""


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
    return response

  @abc.abstractmethod
  def get_response(
    self, request: query_editor.BaseQueryElements, **kwargs: str
  ) -> GarfApiResponse:
    """Method for getting response."""


class RestApiClient(BaseClient):
  """Specifies REST client."""

  OK = 200

  def __init__(self, endpoint: str, **kwargs: str) -> None:
    """Initializes RestApiClient."""
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

  def __init__(self, results: Sequence[dict[str, Any]], **kwargs: str) -> None:
    """Initializes FakeApiClient."""
    self.results = list(results)
    self.kwargs = kwargs

  @override
  def get_response(
    self, request: query_editor.BaseQueryElements, **kwargs: str
  ) -> GarfApiResponse:
    del request
    return GarfApiResponse(results=self.results)

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
