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


import garf.core
import pytest
from garf.actors import actor


class TestActor:
  @pytest.fixture
  def test_actor(self):
    return actor.load_actor(source='fake', actor_name='Faker')

  def test_act(self, test_actor):
    report = garf.core.GarfReport(results=[[1]], column_names=['test'])
    result = test_actor.act(report)
    expected_result = actor.ActionResult(num_actions=len(report))
    assert result.num_actions == expected_result.num_actions
