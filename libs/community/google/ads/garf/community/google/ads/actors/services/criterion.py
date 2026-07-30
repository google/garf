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

from garf.community.google.ads.actors.models.criterion import Criterion
from garf.community.google.ads.actors.services import base_service
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
      # FIXME: Build not hardcode
      resource_name = f'customers/{customer_id}/adGroups/{ad_group_id}'
      operation.create.ad_group = resource_name
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
