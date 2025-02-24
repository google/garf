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
"""Module for defining various parsing strategy for API response."""

from __future__ import annotations

import abc
import contextlib
import functools
import operator
from collections.abc import Mapping, MutableSequence
from typing import Any, Union

from typing_extensions import TypeAlias, override

from garf_core import api_clients, exceptions, query_editor

ApiRowElement: TypeAlias = Union[int, float, str, bool, list, None]


class BaseParser(abc.ABC):
  """An interface for all parsers to implement."""

  def parse_response(
    self,
    response: api_clients.GarfApiResponse,
    query_specification: query_editor.BaseQueryElements,
  ) -> list[list[ApiRowElement]]:
    """Parses response."""
    if not response.results:
      return [[]]
    results = []
    for result in response.results:
      results.append(self.parse_row(result, query_specification))
    return results

  @abc.abstractmethod
  def parse_row(self, row, query_specification):
    """Parses single row from response."""


class ListParser(BaseParser):
  """Returns API results as is."""

  @override
  def parse_row(
    self,
    row: list,
    query_specification: query_editor.BaseQueryElements,
  ) -> list[list[ApiRowElement]]:
    return row


class DictParser(BaseParser):
  """Extracts nested dict elements."""

  @override
  def parse_row(
    self,
    row: list,
    query_specification: query_editor.BaseQueryElements,
  ) -> list[list[ApiRowElement]]:
    if not isinstance(row, Mapping):
      raise GarfParserError
    result = []
    for field in query_specification.fields:
      result.append(self.get_nested_field(row, field))
    return result

  def get_nested_field(self, dictionary: dict[str, Any], key: str):
    """Returns nested fields from a dictionary."""
    key = key.split('.')
    try:
      return functools.reduce(operator.getitem, key, dictionary)
    except KeyError:
      return None


class NumericConverterDictParser(DictParser):
  """Extracts nested dict elements with numerical conversions."""

  def get_nested_field(self, dictionary: dict[str, Any], key: str):
    """Extract nested field with int/float conversion."""

    def convert_field(value):
      for type_ in (int, float):
        with contextlib.suppress(ValueError):
          return type_(value)
      return value

    key = key.split('.')
    try:
      field = functools.reduce(operator.getitem, key, dictionary)
      if isinstance(field, MutableSequence) or field in (True, False):
        return field
      return convert_field(field)
    except KeyError:
      return None


class GarfParserError(exceptions.GarfError):
  """Incorrect data format for parser."""
