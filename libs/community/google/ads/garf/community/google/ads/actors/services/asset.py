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
import re

from garf.community.google.ads.actors.models.asset import Asset
from garf.community.google.ads.actors.services import base_service
from google.api_core import protobuf_helpers
from typing_extensions import override


class AssetService(base_service.BaseService):
  """Handles working with assets in Google Ads."""

  def add(self, *assets: Asset) -> list:
    """Create operations for adding assets."""
    return [asset.to_operation(self.client) for asset in assets]

  def update(self, customer_id, asset_id, new_asset: Asset):
    asset_type = _camel_to_snake(new_asset.__class__.__name__.lower())
    asset_operation = self.client.get_type('AssetOperation')
    asset = asset_operation.update
    # TODO: Validate if exits
    asset.resource_name = f'customers/{customer_id}/assets/{asset_id}'
    setattr(
      asset, f'{asset_type}_asset', new_asset.model_dump(exclude_none=True)
    )
    if new_asset.url:
      asset.final_urls.append(str(new_asset.url))

    field_mask = protobuf_helpers.field_mask(None, asset._pb)
    self.client.copy_from(asset_operation.update_mask, field_mask)
    return asset_operation

  @override
  def apply_operations(self, customer_id, operations):
    """Adds assets to account."""
    asset_service = self.client.get_service('AssetService')
    response = asset_service.mutate_assets(
      customer_id=customer_id,
      operations=operations,
    )
    return [result.resource_name for result in response.results]


def _camel_to_snake(text):
  str1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', text)
  return re.sub('([a-z0-9])([A-Z])', r'\1_\2', str1).lower()
