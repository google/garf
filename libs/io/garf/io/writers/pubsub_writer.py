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

import json
import logging
import os

from garf.core import report as garf_report
from garf.io.telemetry import tracer
from garf.io.writers import abs_writer

try:
  from google.cloud import pubsub_v1
except ImportError as e:
  raise ImportError(
    'Please install garf-io with PubSub support - `pip install garf-io[pubsub]`'
  ) from e

logger = logging.getLogger(__name__)


class PubSubWriter(abs_writer.AbsWriter):
  """Publishes Garf Report to a pubsub topic.

  Attributes:
    topic_id: Id of PubSub topic.
  """

  def __init__(
    self,
    project: str = os.getenv('GOOGLE_CLOUD_PROJECT'),
    **kwargs: str,
  ) -> None:
    """Initializes PubSubWriter based on project."""
    super().__init__(**kwargs)
    self.project = project
    self._publisher = None

  @property
  def publisher(self) -> pubsub_v1.PublisherClient:
    if not self._publisher:
      self._publisher = pubsub_v1.PublisherClient()
    return self._publisher

  @tracer.start_as_current_span('pubsub.write')
  def write(self, report: garf_report.GarfReport, destination: str) -> None:
    topic_path = self.publisher.topic_path(self.project, destination)
    if not self.publisher.get_topic(request={'topic': topic_path}):
      self.publisher.create_topic(request={'name': topic_path})
    future = self.publisher.publish(
      topic_path, json.dumps(report.to_list('dict')).encode('utf-8')
    )
    return f'[Pubsub] - published message ID {future.result()}'
