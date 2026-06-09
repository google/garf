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
"""Writes GarfReport to Firestore."""

import logging
import os
from typing import Any

from garf.io.writers import nosql_writer

try:
  from google.cloud import firestore
except ImportError as e:
  raise ImportError(
    'Please install garf-io with Firestore support - '
    '`pip install garf-io[firestore]`'
  ) from e

logger = logging.getLogger(__name__)


class FirestoreWriter(nosql_writer.NoSqlWriter):
  """Publishes Garf Report to a Firestore collection.

  Attributes:
    project: Google Cloud project name.
    db: Name of the database:
  """

  def __init__(
    self,
    project: str = os.getenv('GOOGLE_CLOUD_PROJECT'),
    db: str = '(default)',
    push_strategy: nosql_writer.PushStrategy = nosql_writer.PushStrategy.BATCH,
    batch_size: int = 1000,
    **kwargs: str,
  ) -> None:
    """Initializes FirestoreWriter."""
    super().__init__(
      provider='firestore',
      push_strategy=push_strategy,
      batch_size=batch_size,
      **kwargs,
    )
    self.project = project
    self.db = db
    self._client = None

  @property
  def client(self):
    if not self._client:
      self._client = firestore.Client(project=self.project, database=self.db)
    return self._client

  def _write(self, data: list[dict[str, Any]], collection_name: str):
    """Writes data to Firestore collection.

    Args:
      data: Documents to insert.
      collection_name: Collection to insert documents.
    """
    client = self.client
    batch = client.batch()
    collection_ref = client.collection(collection_name)
    for row in data:
      doc_ref = collection_ref.document()
      batch.set(doc_ref, row)
    return batch.commit()
