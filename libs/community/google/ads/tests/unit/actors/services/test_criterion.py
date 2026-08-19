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


from garf.community.google.ads.actors.models.criterion import Keyword, Placement
from garf.community.google.ads.actors.services.criterion import (
  AdGroupCriterionService,
  CampaignCriterionService,
)


class TestCampaignCriterionService:
  def test_add(self, test_client):
    placements = [
      Placement(type='YOUTUBE_VIDEO', placement='12345678900', negative=True),
      Placement(type='YOUTUBE_VIDEO', placement='12345678901', negative=True),
    ]
    service = CampaignCriterionService(client=test_client)
    operation = service.add(customer_id=1, campaign_id=1, criteria=placements)
    assert len(operation) == len(placements)

  def test_update(self, test_client):
    keywords = [
      Keyword(criterion_id=1, text='test'),
    ]
    service = AdGroupCriterionService(client=test_client)
    operations = service.pause(customer_id=1, ad_group_id=1, criteria=keywords)
    assert operations[0].update.status.name == 'PAUSED'

  def test_delete(self, test_client):
    keywords = [
      Keyword(criterion_id=1, text='test'),
    ]
    service = AdGroupCriterionService(client=test_client)
    operations = service.delete(customer_id=1, ad_group_id=1, criteria=keywords)
    assert operations[0].update.status.name == 'REMOVED'
