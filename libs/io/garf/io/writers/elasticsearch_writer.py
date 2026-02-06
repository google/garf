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
"""Writes GarfReport to Elasticsearch index."""

import logging
from typing import Any, List, Union

from garf.core import report as garf_report
from garf.io.telemetry import tracer
from garf.io.writers import abs_writer

try:
  from elasticsearch import Elasticsearch, helpers
except ImportError as e:
  raise ImportError(
    'Please install garf-io with Elasticsearch support - '
    '`pip install garf-io[elasticsearch]`'
  ) from e

logger = logging.getLogger(__name__)


class ElasticsearchWriter(abs_writer.AbsWriter):
  """Writes Garf Report to Elasticsearch.

  Attributes:
    client: Elasticsearch client.
  """

  def __init__(
    self,
    hosts: Union[List[str], str] = 'localhost:9200',
    http_auth: Any = None,
    **kwargs: Any,
  ) -> None:
    """Initializes ElasticsearchWriter.

    Args:
      hosts: Elasticsearch hosts.
      http_auth: Authentication credentials (user, password) or similar.
      **kwargs: Other arguments for Elasticsearch client.
    """
    super().__init__(**kwargs)
    if isinstance(hosts, str):
      hosts = hosts.split(',')

    self.client = Elasticsearch(hosts=hosts, http_auth=http_auth, **kwargs)

  def _create_index_if_not_exists(self, index_name: str) -> None:
    """Creates index if it does not exist."""
    if not self.client.indices.exists(index=index_name):
      self.client.indices.create(index=index_name)
      logger.info(f'Created index {index_name}')

  @tracer.start_as_current_span('elasticsearch.write')
  def write(self, report: garf_report.GarfReport, destination: str) -> str:
    """Writes report to Elasticsearch.

    Args:
      report: GarfReport to write.
      destination: Elasticsearch index name.
    """
    self._create_index_if_not_exists(destination)

    data = report.to_list(row_type='dict')
    actions = [{'_index': destination, '_source': row} for row in data]

    success, failed = helpers.bulk(self.client, actions)
    return (
      f'[Elasticsearch] - successfully indexed {success} documents to '
      f'{destination}. Failed: {failed}'
    )
