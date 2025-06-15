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

import pydantic

from garf_core import query_editor, report_fetcher
from garf_executors import exceptions
from garf_io import writer
from garf_io.writers import abs_writer

logger = logging.getLogger(__name__)


class ApiExecutionContext(pydantic.BaseModel):
  """Common context for executing one or more queries.

  Attributes:
    query_parameters: Parameters to dynamically change query text.
    fetcher_parameters: Parameters to specify fetching setup.
    writer: Type of writer to use.
    writer_parameters: Optional parameters to setup writer.
  """

  query_parameters: query_editor.GarfQueryParameters | None = None
  fetcher_parameters: dict[str, str] | None = None
  writer: str = 'console'
  writer_parameters: dict[str, str] | None = None

  def model_post_init(self, __context__) -> None:
    if self.fetcher_parameters is None:
      self.fetcher_parameters = {}
    if self.writer_parameters is None:
      self.writer_parameters = {}

  @property
  def writer_client(self) -> abs_writer.AbsWriter:
    writer_client = writer.create_writer(self.writer, **self.writer_parameters)
    if self.writer == 'bq':
      _ = writer_client.create_or_get_dataset()
    if self.writer == 'sheet':
      writer_client.init_client()
    return writer_client


class ApiQueryExecutor:
  """Gets data from API and writes them to local/remote storage.

  Attributes:
      api_client: a client used for connecting to API.
  """

  def __init__(self, fetcher: report_fetcher.ApiReportFetcher) -> None:
    """Initializes ApiQueryExecutor.

    Args:
        fetcher: Instantiated report fetcher.
    """
    self.fetcher = fetcher

  async def aexecute(
    self, query: str, context: ApiExecutionContext, **kwargs: str
  ) -> None:
    """Reads query, extract results and stores them in a specified location.

    Args:
      query: Location of the query.
      context: Query execution context.
    """
    self.execute(query, context, **kwargs)

  def execute(
    self,
    query: str,
    title: str,
    context: ApiExecutionContext,
  ) -> None:
    """Reads query, extract results and stores them in a specified location.

    Args:
      query: Location of the query.
      title: Name of the query.
      context: Query execution context.

    Raises:
      GarfExecutorError: When failed to execute query.
    """
    try:
      logger.debug('starting query %s', query)
      results = self.fetcher.fetch(
        query_specification=query,
        args=context.query_parameters,
        **context.fetcher_parameters,
      )
      writer_client = context.writer_client
      logger.debug(
        'Start writing data for query %s via %s writer',
        title,
        type(writer_client),
      )
      writer_client.write(results, title)
      logger.debug(
        'Finish writing data for query %s via %s writer',
        title,
        type(writer_client),
      )
      logger.info('%s executed successfully', title)
    except Exception as e:
      logger.error('%s generated an exception: %s', title, str(e))
      raise exceptions.GarfExecutorError(
        '%s generated an exception: %s', title, str(e)
      ) from e
