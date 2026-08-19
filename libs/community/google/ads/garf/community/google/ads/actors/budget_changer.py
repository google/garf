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

import logging
from collections import defaultdict

from garf.community.google.ads.actors.services import budget

logger = logging.getLogger(__name__)


class BudgetChanger:
  """Updates campaign budgets."""

  def plan(self, report, **kwargs: str):
    service = budget.BudgetService()
    operations = defaultdict(list)
    for row in report:
      if row.budget_change == 0:
        logger.warning('No budget changes requested')
        break
      if row.budget_change <= -1.0:
        logger.warning('Setting 100% decrease not allowed')
        break
      operation = service.update(
        budget_resource_name=row.budget_resource_name,
        old_budget=row.budget,
        budget_change=row.budget_change,
        max_change_delta=row.max_delta,
      )
      operations[row.customer_id].append(operation)
    return operations, service

  def act(self, report, **kwargs: str):
    operations, service = self.plan(report, **kwargs)
    results = []
    for customer_id, ops in operations.items():
      if ops:
        results.extend(
          service.apply_operations(customer_id=customer_id, operations=ops)
        )
    return results
