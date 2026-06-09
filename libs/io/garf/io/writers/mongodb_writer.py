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
"""Writes GarfReport to MongoDB."""

import logging
from typing import Any

from garf.io.writers import nosql_writer

try:
  import pymongo
except ImportError as e:
  raise ImportError(
    'Please install garf-io with MongoDB support - `pip install garf-io[mongo]`'
  ) from e

logger = logging.getLogger(__name__)


class MongoDbWriter(nosql_writer.NoSqlWriter):
  """Publishes Garf Report to a MongoDb collection.

  Attributes:
    connection_string: str
    db: Name of the database.
  """

  def __init__(
    self,
    connection_string: str = 'mongodb://localhost:27017/',
    db: str = 'garf',
    push_strategy: nosql_writer.PushStrategy = nosql_writer.PushStrategy.BATCH,
    batch_size: int = 1000,
    **kwargs: str,
  ) -> None:
    """Initializes MongoDbWriter."""
    super().__init__(
      provider='mongodb',
      push_strategy=push_strategy,
      batch_size=batch_size,
      **kwargs,
    )
    self.connection_string = connection_string
    self.db = db

  def _init_client(self):
    self.client = pymongo.MongoClient(self.connection_string)

  def _write(self, data: list[dict[str, Any]], collection_name: str):
    """Writes data to MongoDB collection.

    Args:
      data: Documents to insert.
      collection_name: Collection to insert documents.
    """
    collection = pymongo.MongoClient(self.connection_string)[self.db][
      collection_name
    ]
    return collection.insert_many(data)
