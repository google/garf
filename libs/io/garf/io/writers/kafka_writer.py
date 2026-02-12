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

import logging

from garf.io.writers import topic_writer

try:
  from kafka import KafkaProducer
except ImportError as e:
  raise ImportError(
    'Please install garf-io with Kafka support - `pip install garf-io[kafka]`'
  ) from e

logger = logging.getLogger(__name__)
logging.getLogger('kafka.conn').setLevel(logging.WARNING)


class KafkaWriter(topic_writer.TopicWriter):
  """Publishes Garf Report to a Kafka topic.

  Attributes:
    bootstrap_servers: Kafka bootstrap servers.
  """

  def __init__(
    self,
    bootstrap_servers: str = 'localhost:9092',
    push_strategy: topic_writer.PushStrategy = topic_writer.PushStrategy.REPORT,
    batch_size: int = 10,
    **kwargs: str,
  ) -> None:
    """Initializes KafkaWriter."""
    super().__init__(
      provider='kafka',
      push_strategy=push_strategy,
      batch_size=batch_size,
      **kwargs,
    )
    if isinstance(bootstrap_servers, str):
      bootstrap_servers = bootstrap_servers.split(',')
    self.bootstrap_servers = bootstrap_servers

  def _init_producer(self):
    self.producer = KafkaProducer(bootstrap_servers=self.bootstrap_servers)

  def _send(self, data: bytes, topic: str):
    """Writes data to Kafka topic.

    Args:
      data: Bytes to send.
      topic: Kafka topic name.
    """
    self.producer.send(topic=topic, value=data)
