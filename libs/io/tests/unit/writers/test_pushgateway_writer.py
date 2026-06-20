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
from garf.io.writers import pushgateway_writer


class TestPushgatewayWriter:
  def test_convert_report_to_metrics(self):
    namespace = 'test_namespace'
    job = 'test_job'
    metric = 'metric AS field'
    metric2 = 'field AS metric_field_new'
    label = 'dimension'
    label2 = 'dimension2'
    query_spec = garf.core.query_editor.QuerySpecification(
      text=f'SELECT {label}, {label2}, {metric}, {metric2} FROM resource'
    ).generate()
    test_report = garf.core.GarfReport(
      results=[['one', 'two', 1, 2]],
      column_names=[label, label2, 'field', 'metric_field_new'],
      query_specification=query_spec,
    )
    writer = pushgateway_writer.PushgatewayWriter(
      namespace=namespace, endpoint=''
    )
    registry = writer.convert_report_to_metrics(test_report, job)
    expected_metric_name = f'{namespace}_{job}_field'
    expected_metric = registry._names_to_collectors.get(expected_metric_name)
    assert expected_metric
    samples = expected_metric.collect()[0].samples
    assert samples[0].value == 1.0
    assert samples[0].labels == {label: 'one', label2: 'two'}
    expected_metric2_name = f'{namespace}_{job}_field_new'
    expected_metric2 = registry._names_to_collectors.get(expected_metric2_name)
    samples2 = expected_metric2.collect()[0].samples
    assert samples2[0].value == 2.0
    assert samples2[0].labels == {label: 'one', label2: 'two'}

  def test_convert_report_creates_info_metric(self):
    namespace = 'test_namespace'
    job = 'test_job'
    label = 'dimension'
    label2 = 'dimension2'
    query_spec = garf.core.query_editor.QuerySpecification(
      text=f'SELECT {label}, {label2} FROM resource'
    ).generate()
    test_report = garf.core.GarfReport(
      results=[['one', 'two']],
      column_names=[label, label2],
      query_specification=query_spec,
    )
    writer = pushgateway_writer.PushgatewayWriter(
      namespace=namespace, endpoint=''
    )
    registry = writer.convert_report_to_metrics(test_report, job)
    expected_metric_name = f'{namespace}_{job}_info'
    expected_metric = registry._names_to_collectors.get(expected_metric_name)
    assert expected_metric
    samples = expected_metric.collect()[0].samples
    assert samples[0].value == 1.0
    assert samples[0].labels == {label: 'one', label2: 'two'}
