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
from __future__ import annotations

import pytest
from garf.core import GarfReport
from garf.core.query_editor import QuerySpecification
from garf.exporter.exporter import GarfExporter
from prometheus_client import samples


class TestGarfExporter:
  @pytest.fixture
  def test_exporter(self):
    return GarfExporter(namespace='test')

  @pytest.fixture
  def report(self):
    query = 'SELECT campaign.id, metrics.clicks AS clicks FROM campaign'
    query_specification = QuerySpecification(query).generate()
    return GarfReport(
      results=[
        [1, 10],
        [2, 20],
      ],
      column_names=[
        'campaign_id',
        'clicks',
      ],
      query_specification=query_specification,
    )

  @pytest.fixture
  def report_with_virtual_column(self):
    query = 'SELECT campaign.id, 1 AS info FROM campaign'
    query_specification = QuerySpecification(query).generate()
    return GarfReport(
      results=[
        [1, 1],
        [2, 1],
      ],
      column_names=[
        'campaign_id',
        'info',
      ],
      query_specification=query_specification,
    )

  def test_test_exporter_has_default_values(self, test_exporter):
    assert test_exporter.namespace
    assert test_exporter.job_name
    assert not test_exporter.registry.get_target_info()

  def test_export_returns_correct_metric_name(self, test_exporter, report):
    test_exporter.export(report)
    metrics = list(test_exporter.registry.collect())
    assert 'test_clicks' in [metric.name for metric in metrics]

  def test_export_returns_correct_metric_name_with_suffix(
    self, test_exporter, report
  ):
    suffix = 'performance'
    test_exporter.export(report=report, suffix=suffix)
    metrics = list(test_exporter.registry.collect())
    assert f'test_{suffix}_clicks' in [metric.name for metric in metrics]

  def test_export_returns_correct_virtual_metric_name(
    self, test_exporter, report_with_virtual_column
  ):
    test_exporter.export(report=report_with_virtual_column)
    metrics = list(test_exporter.registry.collect())
    assert 'test_info' in [metric.name for metric in metrics]

  def test_export_returns_correct_metric_documentation(
    self, test_exporter, report
  ):
    test_exporter.export(report)
    metrics = list(test_exporter.registry.collect())
    assert 'clicks' in [metric.documentation for metric in metrics]

  def test_export_returns_correct_metric_samples(self, test_exporter, report):
    test_exporter.export(report)
    metrics = list(test_exporter.registry.collect())
    for metric in metrics:
      if metric.name == 'test_clicks':
        assert len(metric.samples) == len(report.results)

  @pytest.mark.parametrize(
    'expected_samples',
    [
      [
        samples.Sample(
          name='test_clicks', labels={'campaign_id': '1'}, value=10.0
        ),
        samples.Sample(
          name='test_clicks', labels={'campaign_id': '2'}, value=20.0
        ),
      ]
    ],
  )
  def test_export_returns_correct_metric_samples_values(
    self, test_exporter, report, expected_samples
  ):
    test_exporter.export(report)
    metrics = list(test_exporter.registry.collect())
    for metric in metrics:
      if metric.name == 'test_clicks':
        assert metric.samples == expected_samples
