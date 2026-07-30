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


import pytest
from garf.community.google.ads.actors.models.criterion import Placement
from garf.community.google.ads.actors.services.criterion import (
  CampaignCriterionService,
)
from google.ads.googleads.client import GoogleAdsClient


class TestCampaignCriterionService:
  @pytest.fixture
  def test_client(self, mocker):
    mocker.patch('google.ads.googleads.client.oauth2', return_value=[])
    return GoogleAdsClient(credentials=None, developer_token='')

  def test_add(self, test_client):
    placements = [
      Placement(type='YOUTUBE_VIDEO', placement='12345678900', negative=True),
      Placement(type='YOUTUBE_VIDEO', placement='12345678901', negative=True),
    ]
    service = CampaignCriterionService(client=test_client)
    operation = service.add(customer_id=1, campaign_id=1, criteria=placements)
    assert len(operation) == len(placements)
