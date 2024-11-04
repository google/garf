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
"""Handles query parsing."""

from __future__ import annotations

import contextlib
import dataclasses
import datetime
import logging
import re
from typing import Generator

import jinja2
from dateutil import relativedelta
from typing_extensions import Self

from garf_core import exceptions


@dataclasses.dataclass
class ProcessedField:
  """Helper class to store fields with its customizers.

  Attributes:
    field: Extractable field.
    customizer_type: Type of customizer to be applied to the field.
    customizer_value: Value to be used in customizer.
  """

  field: str
  customizer_type: str | None = None
  customizer_value: int | str | None = None

  @classmethod
  def from_raw(cls, raw_field: str) -> ProcessedField:
    """Process field to extract possible customizers.

    Args:
        raw_field: Unformatted field string value.

    Returns:
        ProcessedField that contains formatted field with customizers.
    """
    raw_field = raw_field.replace(r'\s+', '').strip()
    if _is_quoted_string(raw_field):
      return ProcessedField(field=raw_field)
    if len(resources := cls._extract_resource_element(raw_field)) > 1:
      field_name, resource_index = resources
      return ProcessedField(
        field=field_name,
        customizer_type='resource_index',
        customizer_value=int(resource_index),
      )

    if len(nested_fields := cls._extract_nested_resource(raw_field)) > 1:
      field_name, nested_field = nested_fields
      return ProcessedField(
        field=field_name,
        customizer_type='nested_field',
        customizer_value=nested_field,
      )
    if len(pointers := cls._extract_pointer(raw_field)) > 1:
      field_name, pointer = pointers
      return ProcessedField(
        field=field_name, customizer_type='pointer', customizer_value=pointer
      )
    return ProcessedField(field=raw_field)

  @classmethod
  def _extract_resource_element(cls, line_elements: str) -> list[str]:
    return re.split('~', line_elements)

  @classmethod
  def _extract_pointer(cls, line_elements: str) -> list[str]:
    return re.split('->', line_elements)

  @classmethod
  def _extract_nested_resource(cls, line_elements: str) -> list[str]:
    return re.split(':', line_elements)


@dataclasses.dataclass(frozen=True)
class VirtualColumn:
  """Represents element in Garf query that either calculated or plugged-in.

  Virtual columns allow performing basic manipulation with metrics and
  dimensions (i.e. division or multiplication) as well as adding raw text
  values directly into report.

  Attributes:
    type: Type of virtual column, either build-in or expression.
    value: Value of the field after macro expansion.
    fields: Possible fields participating in calculations.
    substitute_expression: Formatted expression.
  """

  type: str
  value: str
  fields: list[str] | None = None
  substitute_expression: str | None = None

  @classmethod
  def from_raw(cls, field: str, macros: dict) -> VirtualColumn:
    """Converts a field to virtual column."""
    if field.isdigit():
      field = int(field)
    else:
      with contextlib.suppress(ValueError):
        field = float(field)
    if isinstance(field, (int, float)):
      return VirtualColumn(type='built-in', value=field)

    operators = ('/', r'\*', r'\+', ' - ')
    if len(expressions := re.split('|'.join(operators), field)) > 1:
      virtual_column_fields = []
      substitute_expression = field
      for expression in expressions:
        element = expression.strip()
        if True:
          # if self._is_valid_field(element):
          virtual_column_fields.append(element)
          substitute_expression = substitute_expression.replace(
            element, f'{{{element}}}'
          )
      return VirtualColumn(
        type='expression',
        value=field.format(**macros) if macros else field,
        fields=virtual_column_fields,
        substitute_expression=substitute_expression.replace('.', '_'),
      )
    if not _is_quoted_string(field):
      raise exceptions.GarfFieldException(f"Incorrect field '{field}'.")
    field = field.replace("'", '').replace('"', '')
    field = field.format(**macros) if macros else field
    return VirtualColumn(type='built-in', value=field)


@dataclasses.dataclass
class ExtractedLineElements:
  """Helper class for parsing query lines.

  Attributes:
    fields: All fields extracted from the line.
    alias: Optional alias assign to a field.
    virtual_column: Optional virtual column extracted from query line.
    customizer: Optional values for customizers associated with a field.
  """

  field: str | None
  alias: str | None
  virtual_column: VirtualColumn | None
  customizer: dict[str, str | int]

  @classmethod
  def from_query_line(
    cls, line: str, macros: dict = {}
  ) -> ExtractedLineElements:
    field, *alias = re.split(' [Aa][Ss] ', line)
    processed_field = ProcessedField.from_raw(field)
    field = processed_field.field
    if field:
      # if field.is_valid:
      virtual_column = None
    else:
      virtual_column = VirtualColumn.from_raw(field, macros)
    if alias and processed_field.customizer_type:
      customizer = {
        'type': processed_field.customizer_type,
        'value': processed_field.customizer_value,
      }
    else:
      customizer = {}
    if virtual_column and not alias:
      raise exceptions.GarfVirtualColumnException(
        'Virtual attributes should be aliased'
      )
    return ExtractedLineElements(
      field=_format_type_field_name(field)
      if not virtual_column and field
      else None,
      alias=_normalize_column_name(alias[0] if alias else field),
      virtual_column=virtual_column,
      customizer=customizer,
    )


def _format_type_field_name(field_name: str) -> str:
  return re.sub(r'\.type', '.type_', field_name)


def _normalize_column_name(column_name: str) -> str:
  return re.sub(r'\.', '_', column_name)


@dataclasses.dataclass
class BaseQueryElements:
  """Contains raw query and parsed elements.

  Attributes:
      query_title: Title of the query that needs to be parsed.
      query_text: Text of the query that needs to be parsed.
      resource_name: Name of Google Ads API reporting resource.
      fields: Ads API fields that need to be fetched.
      column_names: Friendly names for fields which are used when saving data
      column_names: Friendly names for fields which are used when saving data
      customizers: Attributes of fields that need to be be extracted.
      virtual_columns: Attributes of fields that need to be be calculated.
      is_constant_resource: Whether resource considered a constant one.
      is_builtin_query: Whether query is built-in.
  """

  title: str
  text: str
  resource_name: str | None = None
  fields: list[str] = dataclasses.field(default_factory=list)
  filters: list[str] = dataclasses.field(default_factory=list)
  sorts: list[str] = dataclasses.field(default_factory=list)
  column_names: list[str] = dataclasses.field(default_factory=list)
  customizers: dict[str, dict[str, str]] = dataclasses.field(
    default_factory=dict
  )
  virtual_columns: dict[str, VirtualColumn] = dataclasses.field(
    default_factory=dict
  )

  def __eq__(self, other: BaseQueryElements) -> bool:  # noqa: D105
    return (
      self.column_names,
      self.fields,
      self.resource_name,
      self.customizers,
      self.virtual_columns,
    ) == (
      other.column_names,
      other.fields,
      other.resource_name,
      other.customizers,
      other.virtual_columns,
    )

  @property
  def request(self) -> str:
    """API request."""
    return ','.join(self.fields)


class CommonParametersMixin:
  """Helper mixin to inject set of common parameters to all queries."""

  _common_params = {
    'date_iso': lambda: datetime.date.today().strftime('%Y%m%d'),
    'yesterday_iso': lambda: (
      datetime.date.today() - relativedelta.relativedelta(days=1)
    ).strftime('%Y%m%d'),
    'current_date': lambda: datetime.date.today().strftime('%Y-%m-%d'),
    'current_datetime': lambda: datetime.datetime.today().strftime(
      '%Y-%m-%d %H:%M:%S'
    ),
  }

  @property
  def common_params(self):
    """Instantiates common parameters to the current values."""
    return {key: value() for key, value in self._common_params.items()}


class TemplateProcessorMixin:
  def replace_params_template(
    self, query_text: str, params: dict | None = None
  ) -> str:
    logging.debug('Original query text:\n%s', query_text)
    if params:
      if templates := params.get('template'):
        query_templates = {
          name: value for name, value in templates.items() if name in query_text
        }
        if query_templates:
          query_text = self.expand_jinja(query_text, query_templates)
          logging.debug('Query text after jinja expansion:\n%s', query_text)
        else:
          query_text = self.expand_jinja(query_text, {})
      else:
        query_text = self.expand_jinja(query_text, {})
      if macros := params.get('macro'):
        query_text = query_text.format(**macros)
        logging.debug('Query text after macro substitution:\n%s', query_text)
    else:
      query_text = self.expand_jinja(query_text, {})
    return query_text

  def expand_jinja(
    self, query_text: str, template_params: dict | None = None
  ) -> str:
    file_inclusions = ('% include', '% import', '% extend')
    if any(file_inclusion in query_text for file_inclusion in file_inclusions):
      template = jinja2.Environment(loader=jinja2.FileSystemLoader('.'))
      query = template.from_string(query_text)
    else:
      query = jinja2.Template(query_text)
    if not template_params:
      return query.render()
    for key, value in template_params.items():
      if value:
        if isinstance(value, list):
          template_params[key] = value
        elif len(splitted_param := value.split(',')) > 1:
          template_params[key] = splitted_param
        else:
          template_params[key] = value
      else:
        template_params = ''
    return query.render(template_params)


class QuerySpecification(CommonParametersMixin, TemplateProcessorMixin):
  """Simplifies fetching data from API and its further parsing.

  Attributes:
    text: Query text.
    title: Query title.
    args: Optional parameters to be dynamically injected into query text.
    api_version: Version of Google Ads API.
  """

  def __init__(
    self,
    text: str,
    title: str | None = None,
    args: dict | None = None,
    **kwargs: str,
  ) -> None:
    """Instantiates QuerySpecification based on text, title and optional args.

    Args:
      text: Query text.
      title: Query title.
      args: Optional parameters to be dynamically injected into query text.
      api_version: Version of Google Ads API.
    """
    self.args = args or {}
    self.query = BaseQueryElements(title=title, text=text)

  @property
  def macros(self) -> dict[str, str]:
    """Returns macros with injected common parameters."""
    common_params = dict(self.common_params)
    if macros := self.args.get('macro'):
      common_params.update(macros)
    return common_params

  def generate(self) -> BaseQueryElements:
    return (
      self.remove_comments()
      .expand()
      .extract_resource_name()
      .remove_trailing_comma()
      .extract_fields()
      .extract_filters()
      .extract_sorts()
      .extract_column_names()
      .extract_virtual_columns()
      .extract_customizers()
      .query
    )

  def expand(self) -> Self:
    """Applies necessary transformations to query."""
    query_text = self.expand_jinja(self.query.text, self.args.get('template'))
    try:
      self.query.text = query_text.format(**self.macros).strip()
    except KeyError as e:
      raise exceptions.GarfMacroException(
        f'No value provided for macro {str(e)}.'
      ) from e
    return self

  def remove_comments(self) -> Self:
    """Removes comments and converts text to lines."""
    result: list[str] = []
    multiline_comment = False
    for line in self.query.text.split('\n'):
      if re.match('\\*/', line):
        multiline_comment = False
        continue
      if re.match('/\\*', line) or multiline_comment:
        multiline_comment = True
        continue
      if re.match('^(#|--|//)', line):
        continue
      cleaned_query_line = re.sub(
        ';$', '', re.sub('(--|//).*$', '', line).strip()
      )
      result.append(cleaned_query_line)
    self.query.text = ' '.join(result)
    return self

  def remove_trailing_comma(self) -> Self:
    self.text = re.sub(r',\s+from', ' FROM', self.query.text, re.IGNORECASE)
    return self

  def extract_resource_name(self) -> Self:
    """Finds resource_name in query_text.

    Returns:
      Found resource.

    Raises:
      GarfResourceException: If resource_name isn't found.
    """
    if resource_name := re.findall(
      r'FROM\s+([\w.]+)', self.query.text, flags=re.IGNORECASE
    ):
      self.query.resource_name = str(resource_name[0]).strip()
      return self
    raise exceptions.GarfResourceException(
      f'No resource found in query: {self.query.text}'
    )

  def extract_fields(self) -> Self:
    for line in self._extract_query_lines():
      line_elements = ExtractedLineElements.from_query_line(line)
      if field := line_elements.field:
        self.query.fields.append(field)
    return self

  def extract_filters(self) -> Self:
    if filters := re.findall(
      r'WHERE\s+(.+)(ORDER BY|LIMIT|PARAMETERS)?',
      self.query.text,
      flags=re.IGNORECASE,
    ):
      filters = [
        filter.strip()
        for filter in re.split(' AND ', filters[0][0], flags=re.IGNORECASE)
      ]
      self.query.filters = filters
    return self

  def extract_sorts(self) -> Self:
    if sorts := re.findall(
      r'ORDER BY\s+(.+)(LIMIT|PARAMETERS)?',
      self.query.text,
      flags=re.IGNORECASE,
    ):
      self.query.sorts = re.split('AND', sorts[0][0], flags=re.IGNORECASE)
    return self

  def extract_column_names(self) -> Self:
    for line in self._extract_query_lines():
      line_elements = ExtractedLineElements.from_query_line(line)
      self.query.column_names.append(line_elements.alias)
    return self

  def extract_virtual_columns(self) -> Self:
    for line in self._extract_query_lines():
      line_elements = ExtractedLineElements.from_query_line(line)
      if virtual_column := line_elements.virtual_column:
        self.query.virtual_columns[line_elements.alias] = virtual_column
    return self

  def extract_customizers(self) -> Self:
    for line in self._extract_query_lines():
      line_elements = ExtractedLineElements.from_query_line(line)
      if customizer := line_elements.customizer:
        self.query.customizers[line_elements.alias] = customizer
    return self

  def _extract_query_lines(self) -> Generator[str, None, None]:
    """Helper for extracting fields with aliases from query text.

    Yields:
      Line in query between SELECT and FROM statements.
    """
    selected_rows = re.sub(
      r'\bSELECT\b|FROM .*', '', self.text, flags=re.IGNORECASE
    ).split(',')
    for row in selected_rows:
      if non_empty_row := row.strip():
        yield non_empty_row


def _is_quoted_string(field_name: str) -> bool:
  return (field_name.startswith("'") and field_name.endswith("'")) or (
    field_name.startswith('"') and field_name.endswith('"')
  )
