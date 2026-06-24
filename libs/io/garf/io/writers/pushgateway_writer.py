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
"""Writes GarfReport to Prometheus Pushgateway."""

import logging
import re
import time
from collections import abc
from itertools import zip_longest

import garf.core
import prometheus_client
from garf.io import formatter
from garf.io.telemetry import tracer
from garf.io.writers import abs_writer

logger = logging.getLogger(__name__)


class PushgatewayWriter(abs_writer.AbsWriter):
  """Writes GarfReport to Prometheus Pushgateway.

  Attributes:
    endpoint: Address and port where Pushgateway is running.
    namespace: Common prefix for all metrics sent to Pushgateway.
    job_name: Name of export job in Prometheus.
    expose_metrics_with_zero_values: Whether to include metrics with 0 value.
  """

  def __init__(
    self,
    endpoint: str = 'http://localhost:9091',
    namespace: str = 'garf',
    job: str = 'garf',
    expose_metrics_with_zero_values: bool = False,
    **kwargs,
  ) -> None:
    """Initializes PushgatewayWriter.

    Args:
      endpoint: Address and port where Pushgateway is running.
      namespace: Common prefix for all metrics sent to Pushgateway.
      job: Name of export job in Prometheus.
      expose_metrics_with_zero_values: Whether to include metrics with 0 value.
    """
    self.endpoint = endpoint
    self.namespace = namespace
    self.job = job
    self.expose_metrics_with_zero_values = expose_metrics_with_zero_values
    super().__init__(**kwargs)

  @tracer.start_as_current_span('pushgateway.write')
  def write(self, report: garf.core.GarfReport, destination: str) -> str:
    """Writes report to Pushgateway.

    Args:
      report: GarfReport to write.
      destination: Grouping key in Pushgateway.
    """
    destination = formatter.format_extension(
      destination,
      prefix=self.options.prefix,
      suffix=self.options.suffix,
    )

    registry = self.convert_report_to_metrics(report, destination)
    registry.collect()
    prometheus_client.push_to_gateway(
      self.endpoint,
      job=self.job,
      registry=registry,
      grouping_key={'query': destination},
    )
    return f'[Pushgateway] - {destination}'

  @tracer.start_as_current_span('pushgateway.convert_report_to_metrics')
  def convert_report_to_metrics(
    self, report: garf.core.GarfReport, destination: str
  ) -> None:
    """Prepares metrics based on GarfReport.

    Args:
      report: GarfReport to write.
      destination: Job name.
    """
    registry = prometheus_client.CollectorRegistry()
    report = self.format_for_write(report)
    suffix = destination
    start = time.time()
    export_time_gauge = self._define_gauge(
      name='query_export_time_seconds',
      suffix='Remove',
      registry=registry,
      labelnames=('collector',),
    )
    api_requests_counter = self._define_counter(
      name='api_requests_count', registry=registry
    )
    metrics = self._define_metrics(
      query_specification=report.query_specification,
      suffix=suffix,
      registry=registry,
    )
    labels = self._define_labels(report.query_specification)
    for row in report:
      label_values = []
      for label in labels:
        if isinstance(row.get(label), abc.MutableSequence):
          label_value = ','.join([str(r) for r in row.get(label)])
        else:
          label_value = row.get(label)
        label_values.append(label_value)
      if not metrics:
        self._define_gauge(
          name='info', suffix=suffix, registry=registry, labelnames=labels
        ).labels(*label_values).set(value=1.0)
        continue
      for name, metric in metrics.items():
        if (
          metric_value := getattr(row, name)
          or self.expose_metrics_with_zero_values
        ) and not isinstance(metric_value, str):
          metric.labels(*label_values).set(metric_value)
    end = time.time()
    export_time_gauge.labels(collector=destination).set(end - start)
    api_requests_counter.inc()
    return registry

  def _define_metrics(
    self,
    query_specification: garf.core.query_editor.QuerySpecification,
    suffix: str,
    registry: prometheus_client.CollectorRegistry,
  ) -> dict[str, prometheus_client.Gauge]:
    """Defines metrics to be exposed Prometheus.

    Metrics are defined based on query_specification of report that needs to
    be exposed. It takes into account both virtual and non-virtual columns.

    Args:
      query_specification:
        QuerySpecification that contains all information about the query.
      suffix: Common identifier to be added to a series of metrics.
      registry: Collector registry.

    Returns:
      Mapping between metrics alias in report and Gauge.
    """
    metrics = {}
    labels = self._define_labels(query_specification)
    non_virtual_columns = self._get_non_virtual_columns(query_specification)
    for column, field in zip_longest(
      non_virtual_columns, query_specification.fields
    ):
      if not column or not field or column == '_':
        continue
      if 'metric' in field or 'metric' in column:
        metrics[column] = self._define_gauge(column, suffix, registry, labels)
    if virtual_columns := query_specification.virtual_columns:
      for column, field in virtual_columns.items():
        if column != '_' and ('metric' in field.value or 'metric' in column):
          metrics[column] = self._define_gauge(column, suffix, registry, labels)
    logger.debug('metrics: %s', metrics)
    return metrics

  def _define_labels(
    self, query_specification: garf.core.query_editor.QuerySpecification
  ) -> list[str]:
    """Defines names of labels to be attached to metrics.

    Label names are build based on column names of the report. Later on each
    label name gets its own value (i.e. customer_id=1, campaign_type=DISPLAY).

    Args:
      query_specification:
        QuerySpecification that contains all information about the query.
      suffix: Common identifier to be added to a series of metrics.

    Returns:
      All possible labels names that can be attached to metrics.
    """
    labelnames = []
    non_virtual_columns = self._get_non_virtual_columns(query_specification)
    for column, field in zip_longest(
      non_virtual_columns, query_specification.fields
    ):
      if not column or not field:
        continue
      if 'metric' not in field and 'metric' not in column:
        labelnames.append(str(column))
    for column, virtual_column in query_specification.virtual_columns.items():
      if virtual_column.type == 'built-in':
        labelnames.append(str(column))
    logger.debug('labelnames: %s', labelnames)
    return labelnames

  def _define_gauge(
    self,
    name: str,
    suffix: str,
    registry: prometheus_client.CollectorRegistry,
    labelnames: abc.Sequence[str] = (),
  ) -> prometheus_client.Gauge:
    """Defines Gauge metric to be created in Prometheus and add labels to it.

    Gauge has the following structure '<namespace>_<suffix>_<name>' and might
    look like this `googleads_disappoved_ads_count` meaning that it comes from
    `googleads` namespace (usually common for all metrics), `disapproved_ads`
    signifies that one or several metrics are coming from a single data fetch
    and usually grouped logically, while `count` represent the metric itself.

    Args:
      name: Name of the metric to be exposed to Prometheus (without prefix).
      suffix: Common identifier to be added to a series of metrics.
      registry: Collector registry.
      labelnames: Dimensions attached to metric (i.e. ad_group_id, account).

    Returns:
      An instance of Counter that associated with registry.
    """
    name = re.sub('_?metric_?', '', name)
    if suffix and suffix != 'Remove':
      gauge_name = f'{self.namespace}_{suffix}_{name}'
    else:
      gauge_name = f'{self.namespace}_{name}'
    if gauge_name in registry._names_to_collectors:
      return registry._names_to_collectors.get(gauge_name)
    return prometheus_client.Gauge(
      name=gauge_name,
      documentation=name,
      labelnames=labelnames,
      registry=registry,
    )

  def _define_counter(
    self, name: str, registry: prometheus_client.CollectorRegistry
  ) -> prometheus_client.Counter:
    """Define Counter metric based on provided name.

    Args:
      name: Name of the metric to be exposed to Prometheus (without prefix).
      registry: Collector registry.

    Returns:
      An instance of Counter that associated with registry.
    """
    counter_name = f'{self.namespace}_{name}'
    if counter_name in registry._names_to_collectors:
      return registry._names_to_collectors.get(counter_name)
    return prometheus_client.Counter(
      name=counter_name, documentation=name, registry=registry
    )

  def _get_non_virtual_columns(
    self, query_specification: garf.core.query_editor.QuerySpecification
  ) -> list[str]:
    """Returns all non-virtual columns from query.

    Virtual columns have special handling during the export so they need
    to be removed.

    Args:
      query_specification:
        QuerySpecification that contains all information about the query.

    Returns:
      All columns from the query that are not virtual.
    """
    return [
      column
      for column in query_specification.column_names
      if column not in query_specification.virtual_columns
    ]
