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
from collections.abc import Iterable
from typing import Any

from typing_extensions import override

from garf_core import parsers, report, report_fetcher
from garf_youtube_data_api.api_clients import YouTubeDataApiClient


def _batched(iterable: Iterable[str], chunk_size: int):
  iterator = iter(iterable)
  while chunk := list(itertools.islice(iterator, chunk_size)):
    yield chunk


class YouTubeDataApiReportFetcher(report_fetcher.ApiReportFetcher):
  """Defines report fetcher."""

  def __init__(
    self,
    api_client: YouTubeDataApiClient = YouTubeDataApiClient(),
    parser: parsers.DictParser = parsers.DictParser,
  ) -> None:
    """Initializes YouTubeDataApiReportFetcher."""
    super().__init__(api_client, parser)

  @override
  def fetch(
    self, query_specification, args: dict[str, Any] = None, **kwargs
  ) -> report.GarfReport:
    results = []
    try:
      ids = kwargs.pop('id')
      name = 'id'
    except KeyError:
      ids = kwargs.pop('playlistId')
      name = 'playlistId'
    for batch in _batched(ids, 50):
      if name == 'playlistId':
        batch = batch[0]
      _ids = {name: batch}
      results.append(super().fetch(query_specification, args, **_ids, **kwargs))
    return functools.reduce(operator.add, results)
