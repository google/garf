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
"""Writes GarfReport to Google PubSub topic."""

import logging
import os

from garf.io.writers import topic_writer

try:
  from google.cloud import pubsub_v1
except ImportError as e:
  raise ImportError(
    'Please install garf-io with PubSub support - `pip install garf-io[pubsub]`'
  ) from e

logger = logging.getLogger(__name__)


class PubSubWriter(topic_writer.TopicWriter):
  """Publishes Garf Report to a pubsub topic.

  Attributes:
    topic_id: Id of PubSub topic.
  """

  def __init__(
    self,
    project: str = os.getenv('GOOGLE_CLOUD_PROJECT'),
    push_strategy: topic_writer.PushStrategy = topic_writer.PushStrategy.REPORT,
    batch_size: int = 10,
    **kwargs: str,
  ) -> None:
    """Initializes PubSubWriter based on project."""
    super().__init__(
      provider='pubsub',
      push_strategy=push_strategy,
      batch_size=batch_size,
      **kwargs,
    )
    self.project = project

  def _init_producer(self):
    self.publisher = pubsub_v1.PublisherClient()

  def create_topic(self, topic: str) -> str:
    topic_path = self.publisher.topic_path(self.project, topic)
    if not self.publisher.get_topic(request={'topic': topic_path}):
      self.publisher.create_topic(request={'name': topic_path})
    return topic_path

  def _send(self, data: bytes, topic: str) -> None:
    """Writes data to Google Cloud PubSub topic.

    Args:
      data: Bytes to send.
      topic: PubSub topic name.
    """
    self.publisher.publish(topic=topic, data=data)
