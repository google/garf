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
"""Writes GarfReport to topics."""

import enum
import itertools
import json
import logging

from garf.core import report as garf_report
from garf.io.telemetry import tracer
from garf.io.writers import abs_writer

logger = logging.getLogger(__name__)


class PushStrategy(str, enum.Enum):
  ROW = 'row'
  BATCH = 'batch'
  REPORT = 'report'


class TopicWriter(abs_writer.AbsWriter):
  """Publishes Garf Report to a topic.

  Attributes:
    push_strategy: Strategy for pushing messages to topic.
  """

  def __init__(
    self,
    provider: str,
    push_strategy: PushStrategy == PushStrategy.REPORT,
    batch_size: int = 10,
    **kwargs: str,
  ) -> None:
    """Initializes KafkaWriter."""
    self.provider = provider
    self.push_strategy = push_strategy
    self.batch_size = int(batch_size)

  def _send(self, data: bytes, topic: str) -> str:
    raise NotImplementedError

  def create_topic(self, topic: str) -> str:
    return topic

  def _init_producer(self):
    raise NotImplementedError

  def write(self, report: garf_report.GarfReport, destination: str) -> str:
    """Writes report to Kafka topic.

    Args:
      report: GarfReport to write.
      destination: Kafka topic name.
    """
    self._init_producer()
    with tracer.start_as_current_span('f{self.provider}.write') as span:
      span.set_attribute('writer.type', str(self.push_strategy))
      topic = self.create_topic(topic=destination)
      if self.push_strategy == PushStrategy.REPORT:
        self._send(
          data=json.dumps(report.to_list('dict')).encode('utf-8'),
          topic=topic,
        )
      elif self.push_strategy == PushStrategy.ROW:
        for row in report:
          self._send(
            data=json.dumps(row.to_dict()).encode('utf-8'), topic=topic
          )
      elif self.push_strategy == PushStrategy.BATCH:
        for batch in _batched(report, self.batch_size):
          data = [row.to_dict() for row in batch]
          self._send(data=json.dumps(data).encode('utf-8'), topic=topic)
    return f'[self.provider] - published message to {topic}'


def _batched(report: garf_report.GarfReport, chunk_size: int):
  iterator = iter(report)
  while chunk := tuple(itertools.islice(iterator, chunk_size)):
    yield chunk
