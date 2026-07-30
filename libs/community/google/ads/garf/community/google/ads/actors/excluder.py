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

from collections import defaultdict

from garf.community.google.ads.actors.models.criterion import Keyword, Placement
from garf.community.google.ads.actors.services import criterion as cr


class Excluder:
  """Add negative criteria to Google Ads."""

  exlusion_mapping: dict[str, type[cr.CriterionService]] = {
    'ad_group_id': cr.AdGroupCriterionService,
    'campaign_id': cr.CampaignCriterionService,
  }

  def plan(self, report, workflow_name: str, **kwargs: str):
    if 'ad_group_id' in report.column_names:
      criterion_service = cr.AdGroupCriterionService()
    elif 'campaign_id' in report.column_names:
      criterion_service = cr.CampaignCriterionService()
    operations = defaultdict(list)
    for row in report:
      if workflow_name in ('keywords', 'search_terms'):
        criterion = Keyword(
          text=row.search_term, match_type='EXACT', negative=True
        )
      elif workflow_name == 'placements':
        criterion = Placement(
          type=row.placement_type, placement=row.placement, negative=True
        )
      operation = criterion_service.add(
        customer_id=row.customer_id,
        ad_group_id=row.ad_group_id,
        criteria=[criterion],
      )
      operations[row.customer_id].extend(operation)
    return operations, criterion_service

  def act(self, report, workflow_name: str, **kwargs: str):
    operations, service = self.plan(report, workflow_name, **kwargs)
    results = []
    for customer_id, ops in operations.items():
      if ops:
        results.extend(
          service.apply_operations(customer_id=customer_id, operations=ops)
        )
    return results


class Adder:
  """Add criteria to Google Ads."""

  adder_mapping: dict[str, type[cr.CriterionService]] = {
    'ad_group_id': cr.AdGroupCriterionService,
    'campaign_id': cr.CampaignCriterionService,
  }

  def plan(self, report, workflow_name: str, **kwargs: str):
    if 'ad_group_id' in report.column_names:
      criterion_service = cr.AdGroupCriterionService()
    elif 'campaign_id' in report.column_names:
      criterion_service = cr.CampaignCriterionService()
    operations = defaultdict(list)
    for row in report:
      if workflow_name == 'search_terms':
        criterion = Keyword(text=row.search_term, match_type='EXACT')
      operation = criterion_service.add(
        customer_id=row.customer_id,
        ad_group_id=row.ad_group_id,
        criteria=[criterion],
      )
      operations[row.customer_id].extend(operation)
    return operations, criterion_service

  def act(self, report, workflow_name: str, **kwargs: str):
    operations, service = self.plan(report, workflow_name, **kwargs)
    results = []
    for customer_id, ops in operations.items():
      results.extend(
        service.apply_operations(customer_id=customer_id, operations=ops)
      )
    return results
