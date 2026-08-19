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


from garf.community.google.ads.actors.services.budget import (
  BudgetService,
)


class TestBudgetService:
  def test_update(self, test_client):
    service = BudgetService(client=test_client)
    current_budget = 1.0
    budget_change = -0.5
    operation = service.update(
      budget_resource_name='customers/1/campaignBudgets/1',
      old_budget=current_budget,
      budget_change=budget_change,
    )
    expected_budget = int(current_budget * (1.0 + budget_change) * 1e6)
    assert operation.update.amount_micros == expected_budget

  def test_update_with_limit(self, test_client):
    service = BudgetService(client=test_client)
    current_budget = 100
    budget_change = 1
    max_change = 50
    operation = service.update(
      budget_resource_name='customers/1/campaignBudgets/1',
      old_budget=current_budget,
      budget_change=budget_change,
      max_change_delta=max_change,
    )
    expected_budget = int((current_budget + max_change) * 1e6)
    assert operation.update.amount_micros == expected_budget
