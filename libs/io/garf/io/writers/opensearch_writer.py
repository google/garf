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
"""Writes GarfReport to OpenSearch index."""

from typing import Any, List, Union

try:
  from opensearchpy import OpenSearch, helpers
except ImportError as e:
  raise ImportError(
    'Please install garf-io with OpenSearch support - '
    '`pip install garf-io[opensearch]`'
  ) from e

from garf.io.writers import search_writer


class OpenSearchWriter(search_writer.SearchWriter):
  """Writes Garf Report to OpenSearch.

  Attributes:
    client: OpenSearch client.
  """

  def __init__(
    self,
    hosts: Union[List[str], str] = 'localhost:9200',
    http_auth: Any = None,
    **kwargs: Any,
  ) -> None:
    """Initializes OpenSearchWriter.

    Args:
      hosts: OpenSearch hosts.
      http_auth: Authentication credentials (user, password) or similar.
      **kwargs: Other arguments for OpenSearch client.
    """
    super().__init__(
      client=OpenSearch,
      bulk=helpers.bulk,
      name='OpenSearch',
      hosts=hosts,
      http_auth=http_auth,
      **kwargs,
    )
