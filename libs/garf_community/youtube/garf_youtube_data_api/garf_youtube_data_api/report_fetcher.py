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

"""Defines report fetcher."""

import functools
import itertools
import operator
from collections.abc import Iterable, MutableSequence
from typing import Any, Final

from typing_extensions import override

from garf_core import parsers, report, report_fetcher
from garf_youtube_data_api import builtins, query_editor
from garf_youtube_data_api.api_clients import YouTubeDataApiClient

ALLOWED_FILTERS: Final[set[str]] = (
  'id',
  'regionCode',
  'videoCategoryId',
  'chart',
  'forHandle',
  'forUsername',
  'onBehalfOfContentOwner',
  'playlistId',
  'videoId',
  'channelId',
)

MAX_BATCH_SIZE: Final[int] = 50


def _batched(iterable: Iterable[str], chunk_size: int):
  iterator = iter(iterable)
  while chunk := list(itertools.islice(iterator, chunk_size)):
    yield chunk


class YouTubeDataApiReportFetcher(report_fetcher.ApiReportFetcher):
  """Defines report fetcher."""

  def __init__(
    self,
    api_client: YouTubeDataApiClient | None = None,
    parser: parsers.BaseParser = parsers.NumericConverterDictParser,
    query_spec: query_editor.YouTubeDataApiQuery = (
      query_editor.YouTubeDataApiQuery
    ),
    builtin_queries=builtins.BUILTIN_QUERIES,
    **kwargs: str,
  ) -> None:
    """Initializes YouTubeDataApiReportFetcher."""
    if not api_client:
      api_client = YouTubeDataApiClient()
    super().__init__(api_client, parser, query_spec, builtin_queries, **kwargs)

  @override
  def fetch(
    self,
    query_specification,
    args: dict[str, Any] = None,
    **kwargs,
  ) -> report.GarfReport:
    results = []
    filter_identifier = list(
      set(ALLOWED_FILTERS).intersection(set(kwargs.keys()))
    )
    if len(filter_identifier) == 1:
      name = filter_identifier[0]
      ids = kwargs.pop(name)
      if not isinstance(ids, MutableSequence):
        ids = ids.split(',')
    else:
      return super().fetch(query_specification, args, **kwargs)
    for batch in _batched(ids, MAX_BATCH_SIZE):
      batch_ids = {name: batch[0]} if name != 'id' else {name: batch}
      res = super().fetch(query_specification, args, **batch_ids, **kwargs)
      results.append(res)
    return functools.reduce(operator.add, results)
