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

from garf.community.google.ads.actors.models.criterion import Criterion
from garf.community.google.ads.actors.services import base_service
from google.api_core import protobuf_helpers
from typing_extensions import override


class CriterionService(base_service.BaseService):
  """Manages setting criteria."""


class AdGroupCriterionService(CriterionService):
  """Sets criteria on ad_group level."""

  def add(self, customer_id: int, ad_group_id: int, criteria: list[Criterion]):
    operations = []
    for criterion in criteria:
      operation = criterion.to_operation(
        self.client, 'AdGroupCriterionOperation'
      )
      resource_name = f'customers/{customer_id}/adGroups/{ad_group_id}'
      operation.create.ad_group = resource_name
      operations.append(operation)
    return operations

  def enable(
    self, customer_id: int, ad_group_id: int, criteria: list[Criterion]
  ):
    return self._change_status(
      customer_id, ad_group_id, criteria, status='ENABLED'
    )

  def pause(
    self, customer_id: int, ad_group_id: int, criteria: list[Criterion]
  ):
    return self._change_status(
      customer_id, ad_group_id, criteria, status='PAUSED'
    )

  def delete(
    self, customer_id: int, ad_group_id: int, criteria: list[Criterion]
  ):
    return self._change_status(
      customer_id, ad_group_id, criteria, status='REMOVED'
    )

  def _change_status(
    self,
    customer_id: int,
    ad_group_id: int,
    criteria: list[Criterion],
    status: Literal['PAUSED', 'ENABLED', 'REMOVED'],
  ):
    operations = []
    for criterion in criteria:
      operation = self.client.get_type('AdGroupCriterionOperation')
      updated_criterion = operation.update
      resource_name = (
        f'customers/{customer_id}/adGroupCriteria/'
        f'{ad_group_id}~{criterion.criterion_id}'
      )
      updated_criterion.resource_name = resource_name
      updated_criterion.status = getattr(
        self.client.enums.AdGroupCriterionStatusEnum, status
      )
      field_mask = protobuf_helpers.field_mask(None, updated_criterion._pb)
      self.client.copy_from(operation.update_mask, field_mask)
      operations.append(operation)
    return operations

  @override
  def apply_operations(self, customer_id, operations):
    service = self.client.get_service('AdGroupCriterionService')
    response = service.mutate_ad_group_criteria(
      customer_id=str(customer_id),
      operations=operations,
    )
    return [result.resource_name for result in response.results]


class CampaignCriterionService(CriterionService):
  """Sets criteria on campaign level."""

  def add(self, customer_id: int, campaign_id: int, criteria: list[Criterion]):
    operations = []
    for criterion in criteria:
      operation = criterion.to_operation(
        self.client, 'CampaignCriterionOperation'
      )
      resource_name = f'customers/{customer_id}/campaigns/{campaign_id}'
      operation.create.campaign = resource_name
      operations.append(operation)
    return operations

  @override
  def apply_operations(self, customer_id, operations):
    service = self.client.get_service('CampaignCriterionService')
    response = service.mutate_campaign_criteria(
      customer_id=str(customer_id),
      operations=operations,
    )
    return [result.resource_name for result in response.results]


class CustomerNegativeCriterionService(CriterionService):
  """Sets negative criteria on account level."""

  def add(self, customer_id: int, criteria: list[Criterion]):
    operations = []
    for criterion in criteria:
      if not criterion.negative:
        continue
      operation = criterion.to_operation(
        self.client, 'CustomerNegativeCriterionOperation'
      )
      resource_name = f'customers/{customer_id}'
      operation.create.campaign = resource_name
      operations.append(operation)
    return operations

  @override
  def apply_operations(self, customer_id, operations):
    service = self.client.get_service('CampaignCriterionService')
    response = service.mutate_campaign_criteria(
      customer_id=str(customer_id),
      operations=operations,
    )
    return [result.resource_name for result in response.results]
