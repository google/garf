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

from typing import Literal

from garf.community.google.ads.actors.services import base_service
from google.api_core import protobuf_helpers
from typing_extensions import override


class StatusService(base_service.BaseService):
  """Manages changing status."""


class AdGroupStatusService(StatusService):
  """Changes ad group status."""

  def pause(self, customer_id: int, ad_group_id: int):
    return self._change_status(customer_id, ad_group_id, status='PAUSED')

  def enable(self, customer_id: int, ad_group_id: int):
    return self._change_status(customer_id, ad_group_id, status='ENABLED')

  def delete(self, customer_id: int, ad_group_id: int):
    return self._change_status(customer_id, ad_group_id, status='DELETED')

  def _change_status(
    self,
    customer_id: int,
    ad_group_id: int,
    status: Literal['PAUSED', 'ENABLED', 'DELETED'],
  ):
    operation = self.client.get_type('AdGroupOperation')
    ad_group = operation.update
    resource_name = f'customers/{customer_id}/adGroups/{ad_group_id}'
    ad_group.resource_name = resource_name
    ad_group.status = getattr(self.client.enums.AdGroupStatusEnum, status)
    field_mask = protobuf_helpers.field_mask(None, ad_group._pb)
    self.client.copy_from(operation.update_mask, field_mask)
    return [operation]

  @override
  def apply_operations(self, customer_id, operations):
    service = self.client.get_service('AdGroupService')
    response = service.mutate_ad_groups(
      customer_id=str(customer_id),
      operations=operations,
    )
    return [result.resource_name for result in response.results]


class CampaignStatusService(StatusService):
  """Changes campaign status."""

  def pause(self, customer_id: int, campaign_id: int):
    return self._change_status(customer_id, campaign_id, status='PAUSED')

  def enable(self, customer_id: int, campaign_id: int):
    return self._change_status(customer_id, campaign_id, status='ENABLED')

  def delete(self, customer_id: int, campaign_id: int):
    return self._change_status(customer_id, campaign_id, status='DELETED')

  def _change_status(
    self,
    customer_id: int,
    campaign_id: int,
    status: Literal['PAUSED', 'ENABLED', 'DELETED'],
  ):
    operation = self.client.get_type('CampaignOperation')
    campaign = operation.update
    resource_name = f'customers/{customer_id}/campaigns/{campaign_id}'
    campaign.resource_name = resource_name
    campaign.status = getattr(self.client.enums.CampaignStatusEnum, status)
    field_mask = protobuf_helpers.field_mask(None, campaign._pb)
    self.client.copy_from(operation.update_mask, field_mask)
    return [operation]

  @override
  def apply_operations(self, customer_id, operations):
    service = self.client.get_service('CampaignService')
    response = service.mutate_campaigns(
      customer_id=str(customer_id),
      operations=operations,
    )
    return [result.resource_name for result in response.results]
