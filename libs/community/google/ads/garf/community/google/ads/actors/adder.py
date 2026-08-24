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

from garf.community.google.ads.actors import base
from garf.community.google.ads.actors.models.asset import (
  Sitelink,
  Text,
  Video,
)
from garf.community.google.ads.actors.models.criterion import Keyword
from garf.community.google.ads.actors.services import asset as asset_service
from garf.community.google.ads.actors.services import (
  criterion as criterion_service,
)


class Adder(base.BaseActor):
  """Add criteria to Google Ads."""

  def plan(self, report, workflow_name: str, **kwargs: str):
    if 'ad_group_id' in report.column_names:
      service = criterion_service.AdGroupCriterionService(client=self.client)
    elif 'campaign_id' in report.column_names:
      service = criterion_service.CampaignCriterionService(client=self.client)
    else:
      service = asset_service.AssetService(client=self.client)
    operations = defaultdict(list)
    for row in report:
      if workflow_name in ('search_terms', 'keywords'):
        criterion = Keyword(text=row.search_term, match_type=row.match_type)
        identifiers = {
          'customer_id': row.customer_id,
          'ad_group_id': row.ad_group_id,
          'criteria': [criterion],
        }
      elif workflow_name == 'sitelinks':
        sitelink = Sitelink(
          link_text=row.sitelink,
          url=row.url,
          description1=row.description1,
          description2=row.description2,
        )
        identifiers = {
          'assets': [sitelink],
        }
      elif workflow_name == 'texts':
        identifiers = {
          'assets': [Text(text=row.text)],
        }
      elif workflow_name == 'videos':
        identifiers = {
          'assets': [Video(video_id=row.video_id, title=row.title)],
        }
      operation = service.add(**identifiers)
      operations[row.customer_id].extend(operation)
    return operations, service

  def act(self, report, workflow_name: str, **kwargs: str):
    operations, service = self.plan(report, workflow_name, **kwargs)
    results = []
    for customer_id, ops in operations.items():
      if ops:
        results.extend(
          service.apply_operations(customer_id=customer_id, operations=ops)
        )
    return results
