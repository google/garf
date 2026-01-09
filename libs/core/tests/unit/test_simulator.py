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
from garf.core import api_clients, simulator


class TestSimulator:
  @pytest.fixture
  def fake_simulator(self):
    data = [
      {'resource': {'name': 1}, 'field2': 2},
      {'resource': {'name': 10}, 'field2': 2},
    ]

    return simulator.ApiReportSimulator(
      api_client=api_clients.FakeApiClient(
        results=data, results_placeholder=data
      )
    )

  def test_simulate_fake(self, fake_simulator):
    query_spec = 'SELECT resource.name FROM resource'
    simulator_spec = simulator.SimulatorSpecification()
    simulated_report = fake_simulator.simulate(query_spec, simulator_spec)
    assert len(simulated_report) == simulator_spec.n_rows
