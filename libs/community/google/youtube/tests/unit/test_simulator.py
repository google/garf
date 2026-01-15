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
from garf.community.google.youtube import simulator


class TestYouTubeDataApiReportSimulator:
  def test_simulate(self):
    fake_simulator = simulator.YouTubeDataApiReportSimulator()
    query_spec = 'SELECT id, statistics.likeCount AS likes FROM videos'
    simulator_spec = simulator.YouTubeDataApiSimulatorSpecification()
    simulated_report = fake_simulator.simulate(query_spec, simulator_spec)
    assert len(simulated_report) == simulator_spec.n_rows
