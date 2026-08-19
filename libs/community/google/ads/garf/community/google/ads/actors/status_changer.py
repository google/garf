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

from garf.community.google.ads.actors.models.criterion import Keyword
from garf.community.google.ads.actors.services import criterion, status

logger = logging.getLogger(__name__)


class StatusChanger:
  """Updates status of entity (Campaign, AdGroup, Keyword)."""

  def plan(self, report, workflow_name: str, **kwargs: str):
    if 'keyword' in report.column_names:
      status_service = criterion.AdGroupCriterionService()
      entity_id = 'ad_group_id'
    elif 'ad_group_id' in report.column_names:
      status_service = status.AdGroupStatusService()
      entity_id = 'ad_group_id'
    elif 'campaign_id' in report.column_names:
      status_service = status.CampaignStatusService()
      entity_id = 'campaign_id'
    operations = defaultdict(list)
    for row in report:
      identifiers = {'customer_id': row.customer_id, entity_id: row[entity_id]}
      if workflow_name == 'keywords':
        keyword = Keyword(
          text=row.keyword, match_type='EXACT', criterion_id=row.criterion_id
        )
        identifiers.update({'criteria': [keyword]})
      if 'PAUSE' in row.status:
        operation = status_service.pause(**identifiers)
      elif 'DELETE' in row.status:
        operation = status_service.delete(**identifiers)
      elif 'ENABLE' in row.status:
        operation = status_service.enable(**identifiers)
      operations[row.customer_id].extend(operation)
    return operations, status_service

  def act(self, report, workflow_name: str, **kwargs: str):
    operations, service = self.plan(report, workflow_name, **kwargs)
    results = []
    for customer_id, ops in operations.items():
      if ops:
        results.extend(
          service.apply_operations(customer_id=customer_id, operations=ops)
        )
    return results
