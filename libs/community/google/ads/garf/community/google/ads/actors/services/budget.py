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

from garf.community.google.ads.actors.services import base_service
from google.api_core import protobuf_helpers
from typing_extensions import override


class BudgetService(base_service.BaseService):
  """Handles working with budgets in Google Ads."""

  def update(
    self,
    budget_resource_name: str,
    old_budget: float,
    budget_change: float,
    max_change_delta: int = 0,
  ):
    operation = self.client.get_type('CampaignBudgetOperation')
    campaign_budget = operation.update
    campaign_budget.resource_name = budget_resource_name
    new_budget = old_budget * (1 + budget_change)
    if max_change_delta > 0 and (new_budget - old_budget) > max_change_delta:
      new_budget = old_budget + max_change_delta
    campaign_budget.amount_micros = int(new_budget * 1e6)

    field_mask = protobuf_helpers.field_mask(None, campaign_budget._pb)
    self.client.copy_from(operation.update_mask, field_mask)
    return operation

  @override
  def apply_operations(self, customer_id, operations):
    """Applies budget changing operations."""
    service = self.client.get_service('CampaignBudgetService')
    response = service.mutate_campaign_budgets(
      customer_id=str(customer_id),
      operations=operations,
    )
    return [result.resource_name for result in response.results]
