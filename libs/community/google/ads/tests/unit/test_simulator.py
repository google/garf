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
import os

import pytest
from garf_google_ads import simulator


@pytest.mark.skipif(
  not os.getenv('GOOGLE_ADS_CONFIGURATION_FILE_PATH'),
  reason='Env variable GOOGLE_ADS_CONFIGURATION_FILE_PATH is not set',
)
class TestGoogleAdsApiReportSimulator:
  def test_simulate(self):
    fake_simulator = simulator.GoogleAdsApiReportSimulator()
    query_spec = 'SELECT campaign.id, metrics.clicks AS clicks FROM campaign'
    simulator_spec = simulator.GoogleAdsApiSimulatorSpecification()
    simulated_report = fake_simulator.simulate(query_spec, simulator_spec)
    assert len(simulated_report) == simulator_spec.n_rows
