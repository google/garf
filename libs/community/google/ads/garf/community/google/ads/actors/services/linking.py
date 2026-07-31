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
"""Handles linking / unlinking existing assets to campaign / ad_group, etc."""

from garf.community.google.ads.actors.services import base_service
from typing_extensions import override


class AssetLinkingService(base_service.BaseService):
  """Links assets to entities (ad_group, campaign, etc)."""


class CustomerAssetLinkingService(AssetLinkingService):
  """Links assets to account."""

  def add(self, customer_id: int, asset_ids: list[int], field_type: str):
    """Adds assets at account level.

    Args:
      customer_id: Account to add assets to.
      asset_ids: Ids of assets.
      field_type: Type of asset.

    Returns:
      List of operations.
    """
    operations = []
    for asset_id in asset_ids:
      operation = self.client.get_type('CustomerAssetOperation')
      customer_asset = operation.create
      resource_name = f'customers/{customer_id}/asset/{asset_id}'
      customer_asset.asset = resource_name
      customer_asset.field_type = getattr(
        self.client.enums.AssetFieldTypeEnum, field_type
      )
      operations.append(operation)
    return operations

  @override
  def apply_operations(self, customer_id, operations):
    customer_asset_service = self.client.get_service('CustomerAssetService')
    return customer_asset_service.mutate_customer_assets(
      customer_id=customer_id, operations=operations
    )

  def remove(
    self,
    customer_id: int,
    asset_ids: list[int],
    field_type: str,
  ):
    """Remove assets from account.

    Args:
      customer_id: Account to add assets to.
      asset_ids: Ids of assets.
      field_type: Type of asset.

    Returns:
      List of operations.
    """
    operations = []
    for asset_id in asset_ids:
      operation = self.client.get_type('CustomerAssetOperation')
      resource_name = (
        f'customers/{customer_id}/customerAssets/{asset_id}~{field_type}'
      )
      operation.remove = resource_name
      operations.append(operation)
    return operations


class CampaignAssetLinkingService(AssetLinkingService):
  """Links assets to campaign."""

  def add(
    self,
    customer_id: int,
    campaign_id: int,
    asset_ids: list[int],
    field_type: str,
  ):
    """Adds assets to campaign.

    Args:
      customer_id: Account to add assets to.
      campaign_id: Id of campaign.
      asset_ids: Ids of assets.
      field_type: Type of asset.

    Returns:
      List of operations.
    """
    campaign_service = self.client.get_service('CampaignService')
    operations = []
    for asset_id in asset_ids:
      operation = self.client.get_type('CampaignAssetOperation')
      campaign_asset = operation.create
      resource_name = f'customers/{customer_id}/assets/{asset_id}'
      campaign_asset.asset = resource_name
      campaign_asset.campaign = campaign_service.campaign_path(
        customer_id, campaign_id
      )
      campaign_asset.field_type = getattr(
        self.client.enums.AssetFieldTypeEnum, field_type
      )
      operations.append(operation)
    return operations

  @override
  def apply_operations(self, customer_id, operations):
    campaign_asset_service = self.client.get_service('CampaignAssetService')
    return campaign_asset_service.mutate_campaign_assets(
      customer_id=customer_id, operations=operations
    )

  def remove(
    self,
    customer_id: int,
    campaign_id: int,
    asset_ids: list[int],
    field_type: str,
  ):
    """Remove assets from campaign.

    Args:
      customer_id: Account to add assets to.
      campaign_id: Id of campaign.
      asset_ids: Ids of assets.
      field_type: Type of asset.

    Returns:
      List of operations.
    """
    operations = []
    for asset_id in asset_ids:
      operation = self.client.get_type('CampaignAssetOperation')
      resource_name = (
        f'customers/{customer_id}/campaignAssets/'
        f'{campaign_id}~{asset_id}~{field_type}'
      )
      operation.remove = resource_name
      operations.append(operation)
    return operations


class AdGroupAssetLinkingService(AssetLinkingService):
  """Links assets to ad_group."""

  def add(
    self,
    customer_id: int,
    ad_group_id: int,
    asset_ids: list[int],
    field_type: str,
  ):
    """Adds assets to ad_group.

    Args:
      customer_id: Account to add assets to.
      ad_group_id: Id of ad_group.
      asset_ids: Ids of assets.
      field_type: Type of asset.

    Returns:
      List of operations.
    """
    ad_group_service = self.client.get_service('AdGroupService')
    operations = []
    for asset_id in asset_ids:
      operation = self.client.get_type('AdGroupAssetOperation')
      ad_group_asset = operation.create
      resource_name = (
        f'customers/{customer_id}/adGroupAssets/'
        f'{ad_group_id}~{asset_id}~{field_type}'
      )
      ad_group_asset.asset = resource_name
      ad_group_asset.ad_group = ad_group_service.ad_group_path(
        customer_id, ad_group_id
      )
      ad_group_asset.field_type = getattr(
        self.client.enums.AssetFieldTypeEnum, field_type
      )
      operations.append(operation)
    return operations

  @override
  def apply_operations(self, customer_id, operations):
    ad_group_asset_service = self.client.get_service('AdGroupAssetService')
    return ad_group_asset_service.mutate_ad_group_assets(
      customer_id=customer_id, operations=operations
    )

  def remove(
    self,
    customer_id: int,
    ad_group_id: int,
    asset_ids: list[int],
    field_type: str,
  ):
    """Remove assets from ad_group.

    Args:
      customer_id: Account to add assets to.
      ad_group_id: Id of ad_group.
      asset_ids: Ids of assets.
      field_type: Type of asset.

    Returns:
      List of operations.
    """
    operations = []
    for asset_id in asset_ids:
      operation = self.client.get_type('AdGroupAssetOperation')
      resource_name = (
        f'customers/{customer_id}/adGroupAssets/'
        f'{ad_group_id}~{asset_id}~{field_type}'
      )
      operation.remove = resource_name
      operations.append(operation)
    return operations
