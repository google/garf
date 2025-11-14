# Copyright 2025 Google LLf
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

# pylint: disable=C0330, g-bad-import-order, g-multiple-import

"""Module for getting data from API based on a query.

ApiReportFetcher fetches data from API, parses it and returns GarfReport.
"""

from __future__ import annotations

import asyncio
import logging
from typing import Callable

from opentelemetry import trace

from garf_core import (
  api_clients,
  exceptions,
  parsers,
  query_editor,
  report,
)
from garf_core.telemetry import tracer

logger = logging.getLogger(__name__)


class ApiReportFetcherError(exceptions.GarfError):
  """Base exception for all ApiReportFetchers."""


class MissingApiReportFetcherError(ApiReportFetcherError):
  """Exception for not found report fetcher."""

  def __init__(self, source: str) -> None:
    """Initializes MissingApiReportFetcherError."""
    self.source = source

  def __str__(self) -> str:
    return f'No fetcher available for the source "{self.source}"'


class ApiReportFetcher:
  """Class responsible for getting data from report API.

  Attributes:
      api_client: Client used for connecting to API.
      parser: Class of parser to convert API response.
      query_specification_builder: Class to perform query parsing.
      builtin_queries:
        Mapping between query name and function for generating GarfReport.
  """

  def __init__(
    self,
    api_client: api_clients.BaseClient,
    parser: type[parsers.BaseParser] = parsers.DictParser,
    query_specification_builder: type[query_editor.QuerySpecification] = (
      query_editor.QuerySpecification
    ),
    builtin_queries: dict[str, Callable[[ApiReportFetcher], report.GarfReport]]
    | None = None,
    **kwargs: str,
  ) -> None:
    """Instantiates ApiReportFetcher based on provided api client.

    Args:
      api_client: Instantiated api client.
      parser: Type of parser to convert API response.
      query_specification_builder: Class to perform query parsing.
      builtin_queries:
        Mapping between query name and function for generating GarfReport.
    """
    self.api_client = api_client
    self.parser = parser
    self.query_specification_builder = query_specification_builder
    self.query_args = kwargs
    self.builtin_queries = builtin_queries or {}

  def add_builtin_queries(
    self,
    builtin_queries: dict[str, Callable[[ApiReportFetcher], report.GarfReport]],
  ) -> None:
    """Adds new built-in queries to the fetcher."""
    self.builtin_queries.update(builtin_queries)

  async def afetch(
    self,
    query_specification: str | query_editor.QuerySpecification,
    args: query_editor.GarfQueryParameters | None = None,
    **kwargs: str,
  ) -> report.GarfReport:
    """Asynchronously fetches data from API based on query_specification.

    Args:
      query_specification: Query text that will be passed to API
        alongside column_names, customizers and virtual columns.
      args: Arguments that need to be passed to the query.

    Returns:
      GarfReport with results of query execution.
    """
    return await asyncio.to_thread(
      self.fetch, query_specification, args, **kwargs
    )

  @tracer.start_as_current_span('fetch')
  def fetch(
    self,
    query_specification: str | query_editor.QuerySpecification,
    args: query_editor.GarfQueryParameters | None = None,
    **kwargs: str,
  ) -> report.GarfReport:
    """Fetches data from API based on query_specification.

    Args:
      query_specification: Query text that will be passed to API
        alongside column_names, customizers and virtual columns.
      args: Arguments that need to be passed to the query.

    Returns:
      GarfReport with results of query execution.

    Raises:
      GarfExecutorException:
        When customer_ids are not provided or API returned error.
    """
    span = trace.get_current_span()
    if args is None:
      args = query_editor.GarfQueryParameters()
    if not isinstance(query_specification, query_editor.QuerySpecification):
      query_specification = self.query_specification_builder(
        text=str(query_specification),
        args=args,
      )
    query = query_specification.generate()
    if query.is_builtin_query:
      span.set_attribute('is_builtin_query', True)
      if not (builtin_report := self.builtin_queries.get(query.title)):
        raise query_editor.GarfBuiltInQueryError(
          f'Cannot find the built-in query "{query.title}"'
        )
      return builtin_report(self, **kwargs)

    response = self.api_client.call_api(query, **kwargs)
    if not response:
      return report.GarfReport(query_specification=query)

    parsed_response = self.parser(query).parse_response(response)
    return report.GarfReport(
      results=parsed_response,
      column_names=query.column_names,
      query_specification=query,
    )
