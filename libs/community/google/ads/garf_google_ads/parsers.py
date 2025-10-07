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


from __future__ import annotations

import contextlib
import importlib
import operator
import re
from collections import abc
from typing import Union, get_args

import proto  # type: ignore
from garf_core import parsers
from google import protobuf
from proto.marshal.collections import repeated
from typing_extensions import Self, TypeAlias

from garf_google_ads import api_clients, query_editor

google_ads_service = importlib.import_module(
  f'google.ads.googleads.{api_clients.GOOGLE_ADS_API_VERSION}.'
  'services.types.google_ads_service'
)

GoogleAdsRowElement: TypeAlias = Union[int, float, str, bool, list, None]

_REPEATED: TypeAlias = Union[
  repeated.Repeated,
  protobuf.internal.containers.RepeatedScalarFieldContainer,
]
_REPEATED_COMPOSITE: TypeAlias = Union[
  repeated.RepeatedComposite,
  protobuf.internal.containers.RepeatedCompositeFieldContainer,
]

_NESTED_FIELD: TypeAlias = Union[
  _REPEATED,
  _REPEATED_COMPOSITE,
]


class BaseParser:
  """Base class for defining parsers.

  Attributes:
      _successor: Indicates the previous parser in the chain.
  """

  def __init__(self, successor: type[Self]) -> None:
    self._successor = successor

  def parse(self, element: GoogleAdsRowElement) -> GoogleAdsRowElement:
    """Parses GoogleAdsRow by using a successor parser.

    Args:
        element: An element of a GoogleAdsRow.

    Returns:
        Parsed GoogleAdsRow element.
    """
    if self._successor:
      return self._successor.parse(element)
    return None


class RepeatedParser(BaseParser):
  """Parses repeated.Repeated resources."""

  def parse(self, element: GoogleAdsRowElement) -> GoogleAdsRowElement:
    """Parses only repeated elements from GoogleAdsRow.

    If there a repeated resource, applies transformations to each element;
    otherwise delegates parsing of the element to the next parser
    in the chain.

    Args:
        element: An element of a GoogleAdsRow.

    Returns:
        Parsed GoogleAdsRow element.
    """
    if isinstance(element, get_args(_REPEATED)) and 'customer' in str(element):
      items: list[GoogleAdsRowElement] = []
      for item in element:
        items.append(
          ResourceFormatter(item).get_resource_id().clean_resource_id().format()
        )
      return items
    return super().parse(element)


class RepeatedCompositeParser(BaseParser):
  """Parses repeated.RepeatedComposite elements."""

  def parse(self, element):
    """Parses only repeated composite resources from GoogleAdsRow.

    If there a repeated composited resource, applies transformations
    to each element; otherwise delegates parsing of the element
    to the next parser in the chain.

    Args:
        element: An element of a GoogleAdsRow.

    Returns:
        Parsed GoogleAdsRow element.
    """
    if isinstance(element, get_args(_REPEATED_COMPOSITE)):
      items = []
      for item in element:
        items.append(
          ResourceFormatter(item)
          .get_nested_resource()
          .get_resource_id()
          .clean_resource_id()
          .format()
        )
      return items
    return super().parse(element)


class AttributeParser(BaseParser):
  """Parses elements that have attributes."""

  def parse(self, element: GoogleAdsRowElement) -> GoogleAdsRowElement:
    """Parses only elements that have attributes.

    If there a repeated composited resource, applies transformations
    to each element; otherwise delegates parsing of the element
    to the next parser in the chain.

    Args:
        element: An element of a GoogleAdsRow.

    Returns:
        Parsed GoogleAdsRow element.
    """
    if hasattr(element, 'name'):
      return element.name
    if hasattr(element, 'text'):
      return element.text
    if hasattr(element, 'asset'):
      return element.asset
    if hasattr(element, 'value'):
      return element.value
    return super().parse(element)


class EmptyMessageParser(BaseParser):
  """Generates placeholder for empty Message objects."""

  def parse(self, element: GoogleAdsRowElement) -> GoogleAdsRowElement:
    """Checks if an element is an empty proto.Message.

    If an element is empty message, returns 'Not set' placeholder;
    otherwise delegates parsing of the element to the next parser
    in the chain.

    Args:
        element: An element of a GoogleAdsRow.

    Returns:
        Parsed GoogleAdsRow element.
    """
    if issubclass(type(element), proto.Message):
      return 'Not set'
    return super().parse(element)


class GoogleAdsRowParser(parsers.ProtoParser):
  """Performs parsing of a single GoogleAdsRow.

  Attributes:
      fields: Expected fields in GoogleAdsRow.
      customizers: Customizing behaviour performed on a field.
      virtual_columns: Elements that are not directly present in GoogleAdsRow.
      parser: Chain of parsers to execute on a single GoogleAdsRow.
      row_getter: Helper to easily extract fields from GogleAdsRow.
      respect_nulls: Whether or not convert nulls to zeros.
  """

  def __init__(
    self, query_specification: query_editor.QueryElements, **kwargs: str
  ) -> None:
    """Initializes GoogleAdsRowParser.

    Args:
        query_specification: All elements forming gaarf query.
    """
    super().__init__(query_specification, **kwargs)
    self.fields = query_specification.fields
    self.customizers = query_specification.customizers
    self.virtual_columns = query_specification.virtual_columns
    self.column_names = query_specification.column_names
    self.parser_chain = self._init_parsers_chain()
    self.row_getter = operator.attrgetter(*query_specification.fields)
    # Some segments are automatically converted to 0 when not present
    # For this case we specify attribute `respect_null` which converts
    # such attributes to None rather than 0
    self.respect_nulls = (
      'segments.sk_ad_network_conversion_value' in self.fields
    )

  def _init_parsers_chain(self):
    """Initializes chain of parsers."""
    parser_chain = BaseParser(None)
    for parser in [
      EmptyMessageParser,
      AttributeParser,
      RepeatedCompositeParser,
      RepeatedParser,
    ]:
      new_parser = parser(parser_chain)
      parser_chain = new_parser
    return parser_chain

  def parse_row_element(
    self, row: GoogleAdsRowElement, key: str
  ) -> GoogleAdsRowElement:
    """Parses a single element from row.

    Args:
        extracted_attribute: A single element from GoogleAdsRow.
        column: Corresponding name of the element.

    Returns:
        Parsed element.
    """
    getter = operator.attrgetter(key)
    row = getter(row)
    if isinstance(row, abc.MutableSequence):
      parsed_element = [
        self.parser_chain.parse(element) or element for element in row
      ]
    else:
      parsed_element = self.parser_chain.parse(row) or row

    return parsed_element


class ResourceFormatter:
  """Helper class for formatting resources strings."""

  def __init__(self, element: str) -> None:
    """Initializes ResourceFormatter based on element."""
    self.element = str(element).strip()

  def get_nested_resource(self) -> Self:
    """Extract nested resources from the API response field."""
    self.element = re.split(': ', self.element)[1]
    return self

  def get_resource_id(self) -> Self:
    """Extracts last id of resource_name.

    Resource name looks like `customer/123/campaigns/321`.
    `get_resource_id` returns `321`.
    """
    self.element = re.split('/', self.element)[-1]
    return self

  def clean_resource_id(self) -> Self:
    """Ensures that resource_id is cleaned up and converted to int."""
    self.element = re.sub('"', '', self.element)
    with contextlib.suppress(ValueError):
      self.element = int(self.element)
    return self

  def format(self) -> str | int:
    """Final method to return formatted resource.

    Returns:
      Formatted resource.
    """
    return self.element
