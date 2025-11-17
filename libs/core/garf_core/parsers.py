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
import ast
import contextlib
import functools
import operator
from collections.abc import Mapping, MutableSequence
from typing import Any

from garf_core import (
  api_clients,
  exceptions,
  query_editor,
  query_parser,
)
from garf_core.telemetry import tracer

VALID_VIRTUAL_COLUMN_OPERATORS = (
  ast.BinOp,
  ast.UnaryOp,
  ast.operator,
  ast.Constant,
  ast.Expression,
)


class BaseParser(abc.ABC):
  """An interface for all parsers to implement."""

  def __init__(
    self, query_specification: query_editor.BaseQueryElements
  ) -> None:
    """Initializes BaseParser."""
    self.query_spec = query_specification

  def parse_response(
    self,
    response: api_clients.GarfApiResponse,
  ) -> list[list[api_clients.ApiRowElement]]:
    """Parses response."""
    with tracer.start_as_current_span('parse_response') as span:
      if not response.results:
        span.set_attribute('num_results', 0)
        return [[]]
      results = []
      for result in response.results:
        results.append(self.parse_row(result))
      span.set_attribute('num_results', len(results))
      return results

  def _evalute_virtual_column(
    self,
    fields: list[str],
    virtual_column_values: dict[str, Any],
    substitute_expression: str,
  ) -> api_clients.ApiRowElement:
    virtual_column_replacements = {
      field.replace('.', '_'): value
      for field, value in zip(fields, virtual_column_values)
    }
    virtual_column_expression = substitute_expression.format(
      **virtual_column_replacements
    )
    try:
      tree = ast.parse(virtual_column_expression, mode='eval')
      valid = all(
        isinstance(node, VALID_VIRTUAL_COLUMN_OPERATORS)
        for node in ast.walk(tree)
      )
      if valid:
        return eval(
          compile(tree, filename='', mode='eval'), {'__builtins__': None}
        )
    except ZeroDivisionError:
      return 0
    return None

  def process_virtual_column(
    self,
    row: api_clients.ApiResponseRow,
    virtual_column: query_editor.VirtualColumn,
  ) -> api_clients.ApiRowElement:
    if virtual_column.type == 'built-in':
      return virtual_column.value
    virtual_column_values = [
      self.parse_row_element(row, field) for field in virtual_column.fields
    ]
    try:
      result = self._evalute_virtual_column(
        virtual_column.fields,
        virtual_column_values,
        virtual_column.substitute_expression,
      )
    except TypeError:
      virtual_column_values = [
        f"'{self.parse_row_element(row, field)}'"
        for field in virtual_column.fields
      ]
      result = self._evalute_virtual_column(
        virtual_column.fields,
        virtual_column_values,
        virtual_column.substitute_expression,
      )
    except SyntaxError:
      return virtual_column.value
    return result

  def process_customizer(
    self,
    row: api_clients.ApiResponseRow,
    customizer: query_parser.Customizer,
    field: str,
  ) -> api_clients.ApiRowElement:
    if customizer.type == 'slice':
      return self._process_customizer_slice(row, customizer, field)
    return row

  def _process_customizer_slice(self, row, customizer, field):
    slice_object = customizer.value.slice_literal
    return [r.get(customizer.value.value) for r in row.get(field)[slice_object]]

  def parse_row(
    self,
    row: api_clients.ApiResponseRow,
  ) -> list[api_clients.ApiRowElement]:
    """Parses single row from response."""
    results = []
    fields = self.query_spec.fields
    index = 0
    for column in self.query_spec.column_names:
      if column == '_':
        index += 1
        continue
      if virtual_column := self.query_spec.virtual_columns.get(column):
        result = self.process_virtual_column(row, virtual_column)
      elif customizer := self.query_spec.customizers.get(column):
        result = self.process_customizer(row, customizer, fields[index])
      else:
        result = self.parse_row_element(row, fields[index])
        index = index + 1
      results.append(result)
    return results

  @abc.abstractmethod
  def parse_row_element(
    self, row: api_clients.ApiResponseRow, key: str
  ) -> api_clients.ApiRowElement:
    """Returns nested fields from a dictionary."""


class DictParser(BaseParser):
  """Extracts nested dict elements."""

  def parse_row_element(
    self, row: api_clients.ApiResponseRow, key: str
  ) -> api_clients.ApiRowElement:
    """Returns nested fields from a dictionary."""
    if not isinstance(row, Mapping):
      raise GarfParserError
    if result := row.get(key):
      return result
    key = key.split('.')
    try:
      return functools.reduce(operator.getitem, key, row)
    except (TypeError, KeyError):
      return None


class NumericConverterDictParser(DictParser):
  """Extracts nested dict elements with numerical conversions."""

  def parse_row_element(
    self, row: api_clients.ApiResponseRow, key: str
  ) -> api_clients.ApiRowElement:
    """Extract nested field with int/float conversion."""

    def convert_field(value):
      for type_ in (int, float):
        with contextlib.suppress(ValueError):
          return type_(value)
      return value

    if result := row.get(key):
      return convert_field(result)

    key = key.split('.')
    try:
      field = functools.reduce(operator.getitem, key, row)
      if isinstance(field, MutableSequence) or field in (True, False):
        return field
      return convert_field(field)
    except KeyError:
      return None


class GarfParserError(exceptions.GarfError):
  """Incorrect data format for parser."""
