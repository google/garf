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
"""Shared functionality of writing GarfReport to Search index."""

import logging
from typing import Any, List, Union

from garf.core import report as garf_report
from garf.io import formatter
from garf.io.telemetry import tracer
from garf.io.writers import abs_writer

logger = logging.getLogger(__name__)


class SearchWriter(abs_writer.AbsWriter):
  """Writes Garf Report to search index."""

  def __init__(
    self,
    client,
    bulk,
    name: str,
    hosts: Union[List[str], str] = 'localhost:9200',
    http_auth: Any = None,
    user: str | None = None,
    password: str | None = None,
    **kwargs: Any,
  ) -> None:
    """Initializes SearchWriter.

    Args:
      hosts: Search hosts.
      http_auth: Authentication credentials (user, password) or similar.
    """
    super().__init__(**kwargs)
    if isinstance(hosts, str):
      hosts = hosts.split(',')
    if http_auth:
      self.http_auth = http_auth
    elif user and password:
      self.http_auth = (user, password)
    else:
      self.http_auth = None
    self.client = client(hosts=hosts, http_auth=http_auth)
    self.bulk = bulk
    self.name = name

  def _create_index_if_not_exists(self, index_name: str) -> None:
    """Creates index if it does not exist."""
    if not self.client.indices.exists(index=index_name):
      self.client.indices.create(index=index_name)
      logger.info(f'Created index {index_name}')

  def write(self, report: garf_report.GarfReport, destination: str) -> str:
    """Writes report.

    Args:
      report: GarfReport to write.
      destination: Index name.
    """
    with tracer.start_as_current_span(f'{self.name.lower()}.write'):
      report = self.format_for_write(report)
      destination = formatter.format_extension(destination)
      self._create_index_if_not_exists(destination)

      data = report.to_list(row_type='dict')
      actions = [{'_index': destination, '_source': row} for row in data]

      success, failed = self.bulk(self.client, actions)
      return (
        f'[{self.name}] - successfully indexed {success} documents to '
        f'{destination}. Failed: {failed}'
      )
