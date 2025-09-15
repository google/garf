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

"""Getting fake data from memory or a file."""

from __future__ import annotations

import logging
import os
from collections.abc import Sequence
from typing import Any

from garf_core import (
  api_clients,
  parsers,
  query_editor,
  report_fetcher,
)

logger = logging.getLogger(__name__)


class FakeApiReportFetcher(report_fetcher.ApiReportFetcher):
  """Returns simulated data."""

  def __init__(
    self,
    api_client: api_clients.FakeApiClient | None = None,
    parser: parsers.BaseParser = parsers.DictParser,
    query_specification_builder: query_editor.QuerySpecification = (
      query_editor.QuerySpecification
    ),
    data_location: str | os.PathLike[str] | None = None,
    csv_location: str | os.PathLike[str] | None = None,
    json_location: str | os.PathLike[str] | None = None,
    **kwargs: str,
  ) -> None:
    if not api_client and not (
      data_location := json_location or csv_location or data_location
    ):
      raise report_fetcher.ApiReportFetcherError(
        'Missing fake data for the fetcher.'
      )
    if not api_client:
      api_client = api_clients.FakeApiClient.from_file(data_location)
    super().__init__(api_client, parser, query_specification_builder, **kwargs)

  @classmethod
  def from_data(cls, data: Sequence[dict[str, Any]]) -> FakeApiReportFetcher:
    """Initializes FakeApiReportFetcher from a sequence of data."""
    return FakeApiReportFetcher(
      api_client=api_clients.FakeApiClient(results=data)
    )

  @classmethod
  def from_csv(
    cls, file_location: str | os.PathLike[str]
  ) -> FakeApiReportFetcher:
    """Initializes FakeApiReportFetcher from a csv file."""
    return FakeApiReportFetcher(csv_location=file_location)

  @classmethod
  def from_json(
    cls, file_location: str | os.PathLike[str]
  ) -> FakeApiReportFetcher:
    """Initializes FakeApiReportFetcher from a json file."""
    return FakeApiReportFetcher(json_location=file_location)
