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
import dataclasses
import json
import os
import pathlib
from collections.abc import Sequence
from typing import Any

import requests
from typing_extensions import override

from garf_core import exceptions


@dataclasses.dataclass
class GarfApiRequest:
  """Base class for specifying request."""


@dataclasses.dataclass
class GarfApiResponse:
  """Base class for specifying response."""

  results: list


class GarfApiError(exceptions.GarfError):
  """API specific exception."""


class BaseClient(abc.ABC):
  """Base API client class."""

  @abc.abstractmethod
  def get_response(
    self, request: GarfApiRequest = GarfApiRequest(), **kwargs: str
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
    self, request: GarfApiRequest = GarfApiRequest(), **kwargs: str
  ) -> GarfApiResponse:
    response = requests.get(f'{self.endpoint}/{request.resource_name}')
    if response.status_code == self.OK:
      return GarfApiResponse(response.json())
    raise GarfApiError('Failed to get data from API')


class FakeApiClient(BaseClient):
  """Fake class for specifying API client."""

  def __init__(self, results: Sequence[dict[str, Any]], **kwargs: str) -> None:
    """Initializes FakeApiClient."""
    self.results = list(results)
    self.kwargs = kwargs

  @override
  def get_response(
    self, request: GarfApiRequest = GarfApiRequest(), **kwargs: str
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
      with pathlib.Path.open(file_location, 'r', encoding='utf-8') as f:
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
      with pathlib.Path.open(file_location, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        data = []
        for row in reader:
          data.append(
            {key: _field_converter(value) for key, value in row.items()}
          )
        return FakeApiClient(data)
    except FileNotFoundError as e:
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
