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
"""Base class for all services."""

from google.ads.googleads.client import GoogleAdsClient


class BaseService:
  """Base class for all services.

  Attributes:
    client: Initialized Google Ads client.
  """

  def __init__(self, client: GoogleAdsClient | None = None):
    # FIXME: more flexible initialization
    self.client = client or GoogleAdsClient.load_from_storage(
      '~/google-ads.yaml'
    )

  def apply_operations(self, customer_id: int, operations: list) -> list[str]:
    """Applies operations to a specified customer_id.

    Args:
      customer_id: Account number to apply operation to.
      operations: Ads mutate operations.

    Returns:
      Resource names of changed resources.
    """
    raise NotImplementedError
