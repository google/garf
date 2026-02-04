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
"""Defines report fetcher."""

import functools
import itertools
import logging
import operator
from collections.abc import Iterable, MutableSequence
from typing import Final

import garf.core.query_editor
from garf.community.google.youtube import (
  api_clients,
  builtins,
  exceptions,
  query_editor,
  simulator,
)
from garf.core import parsers, report, report_fetcher
from typing_extensions import override

logger = logging.getLogger('garf.community.google.youtube.report_fetcher')

MAX_BATCH_SIZE: Final[int] = 50


def _batched(iterable: Iterable[str], chunk_size: int):
  iterator = iter(iterable)
  while chunk := list(itertools.islice(iterator, chunk_size)):
    yield chunk


class YouTubeDataApiReportFetcherError(exceptions.GarfYouTubeApiError):
  """YouTubeDataApiReportFetcher specific error."""


class YouTubeDataApiReportFetcher(report_fetcher.ApiReportFetcher):
  """Defines report fetcher for YouTube Data API."""

  alias = 'youtube-data-api'

  def __init__(
    self,
    api_client: api_clients.YouTubeDataApiClient | None = None,
    parser: parsers.BaseParser = parsers.NumericConverterDictParser,
    query_spec: query_editor.YouTubeDataApiQuery = (
      query_editor.YouTubeDataApiQuery
    ),
    builtin_queries=builtins.BUILTIN_QUERIES,
    **kwargs: str,
  ) -> None:
    """Initializes YouTubeDataApiReportFetcher."""
    if not api_client:
      api_client = api_clients.YouTubeDataApiClient(**kwargs)
    super().__init__(api_client, parser, query_spec, builtin_queries, **kwargs)

  @override
  def fetch(
    self,
    query_specification: str | query_editor.YouTubeDataApiQuery,
    args: garf.core.query_editor.GarfQueryParameters | None = None,
    title: str | None = None,
    **kwargs,
  ) -> report.GarfReport:
    results = []
    filter_identifier = list(
      set(api_clients.ALLOWED_PARAMETERS).intersection(set(kwargs.keys()))
    )
    if len(filter_identifier) == 1:
      name = filter_identifier[0]
      ids = kwargs.pop(name)
      if not isinstance(ids, MutableSequence):
        ids = ids.split(',')
      if not ids:
        logger.warning('No values provided for %s parameter', name)
        placeholder_report = simulator.YouTubeDataApiReportSimulator(
          api_client=self.api_client,
          parser=self.parser,
          query_spec=self.query_specification_builder,
        ).simulate(
          query_specification=query_specification, args=args, title=title
        )
        return report.GarfReport(
          placeholder_results=placeholder_report.results,
          column_names=placeholder_report.column_names,
        )
    else:
      return super().fetch(
        query_specification=query_specification,
        args=args,
        title=title,
        **kwargs,
      )
    if name == 'id':
      for batch in _batched(ids, MAX_BATCH_SIZE):
        res = super().fetch(
          query_specification=query_specification,
          args=args,
          title=title,
          **{name: batch},
          **kwargs,
        )
        results.append(res)
    else:
      for element in ids:
        res = super().fetch(
          query_specification=query_specification,
          args=args,
          title=title,
          **{name: element},
          **kwargs,
        )
        results.append(res)
    res = functools.reduce(operator.add, results)
    if sorts := (
      query_editor.YouTubeDataApiQuery(text=query_specification)
      .generate()
      .sorts
    ):
      sorts = sorts[0]
      key, *desc = sorts.split(' ')
      asc_order = not desc or 'ASC' in desc[0]
      sorted_report = report.GarfReport.from_pandas(
        res.to_pandas().sort_values(by=key, ascending=asc_order)
      )
      sorted_report.results_placeholder = res.results_placeholder
      return sorted_report
    return res


class YouTubeAnalyticsApiReportFetcher(report_fetcher.ApiReportFetcher):
  """Defines report fetcher for YouTube Analytics API."""

  alias = 'youtube-analytics'

  def __init__(
    self,
    api_client: api_clients.YouTubeAnalyticsApiClient | None = None,
    parser: parsers.DictParser = parsers.DictParser,
    query_spec: query_editor.YouTubeAnalyticsApiQuery = (
      query_editor.YouTubeAnalyticsApiQuery
    ),
    **kwargs: str,
  ) -> None:
    """Initializes YouTubeDataApiReportFetcher."""
    if not api_client:
      api_client = api_clients.YouTubeAnalyticsApiClient()
    super().__init__(api_client, parser, query_spec)
