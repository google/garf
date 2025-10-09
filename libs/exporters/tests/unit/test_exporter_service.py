# Copyright 2025 Google LLC
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

# pylint: disable=C0330, g-bad-import-order, g-multiple-import

import logging
import pathlib

import pytest
from garf_exporter import collector, exporter, exporter_service

_SCRIPT_DIR = pathlib.Path(__file__).parent


class TestGarfExporterService:
  @pytest.fixture(scope='class')
  def service(self):
    return exporter_service.GarfExporterService(
      alias='fake', source_parameters={'csv_location': _SCRIPT_DIR / 'test.csv'}
    )

  def test_generate_metrics_from_collector_name_returns_correct_results(
    self, service, caplog
  ):
    caplog.set_level(logging.INFO)
    test_exporter = exporter.GarfExporter()
    col = collector.Collector(
      title='test', query='SELECT dimension, metric FROM resource'
    )
    test_request = exporter_service.GarfExporterRequest(
      source='fake', collectors=[col]
    )

    service.generate_metrics(test_request, test_exporter)

    assert 'Beginning export' in caplog.text
    assert col.title in caplog.text
    assert 'Export completed' in caplog.text
