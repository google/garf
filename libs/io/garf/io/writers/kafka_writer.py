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
"""Writes GarfReport to Kafka topic."""

import json
import logging

from garf.core import report as garf_report
from garf.io.telemetry import tracer
from garf.io.writers import abs_writer

try:
  from kafka import KafkaProducer
except ImportError as e:
  raise ImportError(
    'Please install garf-io with Kafka support - `pip install garf-io[kafka]`'
  ) from e

logger = logging.getLogger(__name__)
logging.getLogger('kafka.conn').setLevel(logging.WARNING)


class KafkaWriter(abs_writer.AbsWriter):
  """Publishes Garf Report to a Kafka topic.

  Attributes:
    bootstrap_servers: Kafka bootstrap servers.
  """

  def __init__(
    self,
    bootstrap_servers: str = 'localhost:9092',
    **kwargs: str,
  ) -> None:
    """Initializes KafkaWriter."""
    super().__init__(**kwargs)
    if isinstance(bootstrap_servers, str):
      bootstrap_servers = bootstrap_servers.split(',')
    self.bootstrap_servers = bootstrap_servers
    self._producer = None

  @property
  def producer(self) -> KafkaProducer:
    if not self._producer:
      self._producer = KafkaProducer(bootstrap_servers=self.bootstrap_servers)
    return self._producer

  @tracer.start_as_current_span('kafka.write')
  def write(self, report: garf_report.GarfReport, destination: str) -> str:
    """Writes report to Kafka topic.

    Args:
      report: GarfReport to write.
      destination: Kafka topic name.
    """
    future = self.producer.send(
      topic=destination,
      value=json.dumps(report.to_list('dict')).encode('utf-8'),
    )
    result = future.get(timeout=60)
    return (
      f'[Kafka] - published message to {result.topic} '
      'partition {result.partition} offset {result.offset}'
    )
