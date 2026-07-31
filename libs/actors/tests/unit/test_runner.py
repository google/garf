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
from garf.actors import actor, runner


class TestRunner:
  @pytest.fixture
  def test_runner(self):
    return runner.GarfActorRequest(
      rule='value > -1', workflow_name='fake', actor='Faker'
    )

  def test_play(self, test_runner):
    result = test_runner.play()
    expected_result = actor.ActionResult(
      results=None, processed_at=result.processed_at
    )

    assert result == expected_result
