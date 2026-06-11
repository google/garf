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
"""Writes GarfReport to NoSQL DBs."""

import enum
import itertools
import logging
from typing import Any

from garf.core import report as garf_report
from garf.io import formatter
from garf.io.telemetry import tracer
from garf.io.writers import abs_writer

logger = logging.getLogger(__name__)


class PushStrategy(str, enum.Enum):
  ROW = 'row'
  BATCH = 'batch'


class NoSqlWriter(abs_writer.AbsWriter):
  def __init__(
    self,
    provider: str,
    push_strategy: PushStrategy == PushStrategy.BATCH,
    batch_size: int = 1000,
    **kwargs: str,
  ) -> None:
    """Initializes NoSqlWriter."""
    super().__init__(**kwargs)
    self.provider = provider
    self.push_strategy = push_strategy
    self.batch_size = int(batch_size)

  def _write(self, data: list[dict[str, Any]], collection_name: str) -> str:
    raise NotImplementedError

  def write(self, report: garf_report.GarfReport, destination: str) -> str:
    """Writes report to NoSql collection.

    Args:
      report: GarfReport to write.
      destination: collection name.
    """
    with tracer.start_as_current_span(f'{self.provider}.write') as span:
      span.set_attribute('writer.type', str(self.push_strategy))
      destination = formatter.format_extension(
        destination,
        prefix=self.options.prefix,
        suffix=self.options.suffix,
      )
      if self.push_strategy == PushStrategy.ROW:
        for row in report:
          self._write(data=row.to_dict(), collection_name=destination)
      elif self.push_strategy == PushStrategy.BATCH:
        for batch in _batched(report, self.batch_size):
          data = [row.to_dict() for row in batch]
          self._write(data=data, collection_name=destination)
    return f'[{self.provider}] - inserted data to {destination}'


def _batched(report: garf_report.GarfReport, chunk_size: int):
  iterator = iter(report)
  while chunk := tuple(itertools.islice(iterator, chunk_size)):
    yield chunk
