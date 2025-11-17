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

import dataclasses
import datetime
import logging
import re
from typing import Generator, Union

import jinja2
import pydantic
from dateutil import relativedelta
from typing_extensions import Self, TypeAlias

from garf_core import query_parser

logger = logging.getLogger(__name__)

QueryParameters: TypeAlias = dict[str, Union[str, float, int, list]]


class GarfQueryParameters(pydantic.BaseModel):
  """Parameters for dynamically changing text of a query."""

  macro: QueryParameters = pydantic.Field(default_factory=dict)
  template: QueryParameters = pydantic.Field(default_factory=dict)


class GarfMacroError(query_parser.GarfQueryError):
  """Specifies incorrect macro in Garf query."""


class GarfResourceError(query_parser.GarfQueryError):
  """Specifies incorrect resource name in the query."""


class GarfBuiltInQueryError(query_parser.GarfQueryError):
  """Specifies non-existing builtin query."""


@dataclasses.dataclass
class BaseQueryElements:
  """Contains raw query and parsed elements.

  Attributes:
      title: Title of the query that needs to be parsed.
      text: Text of the query that needs to be parsed.
      resource_name: Name of Google Ads API reporting resource.
      fields: Ads API fields that need to be fetched.
      column_names: Friendly names for fields which are used when saving data
      column_names: Friendly names for fields which are used when saving data
      customizers: Attributes of fields that need to be be extracted.
      virtual_columns: Attributes of fields that need to be be calculated.
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
  virtual_columns: dict[str, query_parser.VirtualColumn] = dataclasses.field(
    default_factory=dict
  )
  is_builtin_query: bool = False

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
    self, query_text: str, params: GarfQueryParameters | None = None
  ) -> str:
    logger.debug('Original query text:\n%s', query_text)
    if params:
      if templates := params.template:
        query_templates = {
          name: value for name, value in templates.items() if name in query_text
        }
        if query_templates:
          query_text = self.expand_jinja(query_text, query_templates)
          logger.debug('Query text after jinja expansion:\n%s', query_text)
        else:
          query_text = self.expand_jinja(query_text, {})
      else:
        query_text = self.expand_jinja(query_text, {})
      if macros := params.macro:
        query_text = query_text.format(**macros)
        logger.debug('Query text after macro substitution:\n%s', query_text)
    else:
      query_text = self.expand_jinja(query_text, {})
    return query_text

  def expand_jinja(
    self, query_text: str, template_params: QueryParameters | None = None
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
    args: GarfQueryParameters | None = None,
    **kwargs: str,
  ) -> None:
    """Instantiates QuerySpecification based on text, title and optional args.

    Args:
      text: Query text.
      title: Query title.
      args: Optional parameters to be dynamically injected into query text.
      api_version: Version of Google Ads API.
    """
    self.args = args or GarfQueryParameters()
    self.query = BaseQueryElements(title=title, text=text)

  @property
  def macros(self) -> QueryParameters:
    """Returns macros with injected common parameters."""
    common_params = dict(self.common_params)
    if macros := self.args.macro:
      converted_macros = {
        key: convert_date(value) for key, value in macros.items()
      }
      common_params.update(converted_macros)
    return common_params

  def generate(self) -> BaseQueryElements:
    self.remove_comments().expand().extract_resource_name()
    if self.query.resource_name.startswith('builtin'):
      return BaseQueryElements(
        title=self.query.resource_name.replace('builtin.', ''),
        text=self.query.text,
        resource_name=self.query.resource_name,
        is_builtin_query=True,
      )
    (
      self.remove_trailing_comma()
      .extract_fields()
      .extract_filters()
      .extract_sorts()
      .extract_column_names()
      .extract_virtual_columns()
      .extract_customizers()
    )
    return self.query

  def expand(self) -> Self:
    """Applies necessary transformations to query."""
    query_text = self.expand_jinja(self.query.text, self.args.template)
    try:
      self.query.text = query_text.format(**self.macros).strip()
    except KeyError as e:
      raise GarfMacroError(f'No value provided for macro {str(e)}.') from e
    return self

  def remove_comments(self) -> Self:
    """Removes comments and converts text to lines."""
    result: list[str] = []
    multiline_comment = False
    for raw_line in self.query.text.split('\n'):
      line = raw_line.strip()
      if re.match('\\*/', line):
        multiline_comment = False
        continue
      if re.match('/\\*', line) or multiline_comment:
        multiline_comment = True
        continue
      if re.match('^(#|--|//) ', line) or line in ('--', '#', '//'):
        continue
      cleaned_query_line = re.sub(
        ';$', '', re.sub('(--|//) .*$', '', line).strip()
      )
      result.append(cleaned_query_line)
    self.query.text = ' '.join(result)
    return self

  def remove_trailing_comma(self) -> Self:
    self.text = re.sub(
      r',\s+from', ' FROM', self.query.text, count=0, flags=re.IGNORECASE
    )
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
    raise GarfResourceError(f'No resource found in query: {self.query.text}')

  def extract_fields(self) -> Self:
    for line in self._extract_query_lines():
      line_elements = query_parser.ExtractedLineElements.from_query_line(line)
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
      line_elements = query_parser.ExtractedLineElements.from_query_line(line)
      self.query.column_names.append(line_elements.alias)
      if set(self.query.column_names) == {
        '_',
      } and len(self.query.fields) == len(self.query.column_names):
        raise query_parser.GarfQueryError(
          'At least one column should be included into a query.'
        )
    return self

  def extract_virtual_columns(self) -> Self:
    for line in self._extract_query_lines():
      line_elements = query_parser.ExtractedLineElements.from_query_line(line)
      if virtual_column := line_elements.virtual_column:
        self.query.virtual_columns[line_elements.alias] = virtual_column
        if fields := virtual_column.fields:
          for field in fields:
            if field not in self.query.fields:
              self.query.fields.append(field)
    return self

  def extract_customizers(self) -> Self:
    for line in self._extract_query_lines():
      line_elements = query_parser.ExtractedLineElements.from_query_line(line)
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


def convert_date(date_string: str) -> str:
  """Converts specific dates parameters to actual dates.

  Returns:
    Date string in YYYY-MM-DD format.

  Raises:
    GarfMacroError:
     If dynamic lookback value (:YYYYMMDD-N) is incorrect.
  """
  if isinstance(date_string, list) or date_string.find(':Y') == -1:
    return date_string
  current_date = datetime.date.today()
  base_date, *date_customizer = re.split('\\+|-', date_string)
  if len(date_customizer) > 1:
    raise GarfMacroError(
      'Invalid format for date macro, should be in :YYYYMMDD-N format'
    )
  if not date_customizer:
    days_lookback = 0
  else:
    try:
      days_lookback = int(date_customizer[0])
    except ValueError as e:
      raise GarfMacroError(
        'Must provide numeric value for a number lookback period, '
        'i.e. :YYYYMMDD-1'
      ) from e
  if base_date == ':YYYY':
    new_date = datetime.datetime(current_date.year, 1, 1)
    delta = relativedelta.relativedelta(years=days_lookback)
  elif base_date == ':YYYYMM':
    new_date = datetime.datetime(current_date.year, current_date.month, 1)
    delta = relativedelta.relativedelta(months=days_lookback)
  elif base_date == ':YYYYMMDD':
    new_date = current_date
    delta = relativedelta.relativedelta(days=days_lookback)
  else:
    raise GarfMacroError(
      'Invalid format for date macro, should be in :YYYYMMDD-N format'
    )

  if '-' in date_string:
    return (new_date - delta).strftime('%Y-%m-%d')
  return (new_date + delta).strftime('%Y-%m-%d')
