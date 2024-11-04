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
"""Module for executing Garf queries and writing them to local/remote.

ApiQueryExecutor performs fetching data from API in a form of
GarfReport and saving it to local/remote storage.
"""
# pylint: disable=C0330, g-bad-import-order, g-multiple-import

from __future__ import annotations

import logging

from garf_core import report_fetcher
from garf_io.writers import abs_writer, console_writer

logger = logging.getLogger(__name__)


class ApiQueryExecutor:
  """Gets data from API and writes them to local/remote storage.

  Attributes:
      api_client: a client used for connecting to API.
  """

  def __init__(self, fetcher: report_fetcher.ApiReportFetcher) -> None:
    """Initializes QueryExecutor.

    Args:
        fetcher: Instantiated report fetcher.
    """
    self.fetcher = fetcher

  async def aexecute(
    self,
    query_text: str,
    query_name: str,
    writer_client: abs_writer.AbsWriter = console_writer.ConsoleWriter(),
    args: dict[str, str] | None = None,
    **kwargs: str,
  ) -> None:
    """Reads query, extract results and stores them in a specified location.

    Args:
        query_text: Text for the query.
        query_name: Identifier of a query.
        customer_ids: All accounts for which query will be executed.
        writer_client: Client responsible for writing data to local/remote
            location.
        args: Arguments that need to be passed to the query.
        optimize_performance: strategy for speeding up query execution
            ("NONE", "PROTOBUF", "BATCH", "BATCH_PROTOBUF").
    """
    self.execute(query_text, query_name, writer_client, args, **kwargs)

  def execute(
    self,
    query_text: str,
    query_name: str,
    writer_client: abs_writer.AbsWriter = console_writer.ConsoleWriter(),
    args: dict[str, str] | None = None,
    **kwargs: str,
  ) -> None:
    """Reads query, extract results and stores them in a specified location.

    Args:
        query_text: Text for the query.
        query_name: Identifier of a query.
        writer_client: Client responsible for writing data to local/remote
            location.
        args: Arguments that need to be passed to the query.
    """
    results = self.fetcher.fetch(
      query_specification=query_text, args=args, **kwargs
    )
    logger.debug(
      'Start writing data for query %s via %s writer',
      query_name,
      type(writer_client),
    )
    writer_client.write(results, query_name)
    logger.debug(
      'Finish writing data for query %s via %s writer',
      query_name,
      type(writer_client),
    )
