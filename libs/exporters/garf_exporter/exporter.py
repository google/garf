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

"""GarfExporter is responsible for preparing data for Prometheus."""

from __future__ import annotations

import logging
import time
from collections import abc
from collections.abc import Sequence

import garf_core
import prometheus_client

logger = logging.getLogger(__name__)


class GarfExporter:
  """Exposes reports from Ads API in Prometheus format.

  Attributes:
    namespace: Global prefix for all Prometheus metrics.
    job_name: Name of export job in Prometheus.
    expose_metrics_with_zero_values: Whether to send zero metrics.
  """

  def __init__(
    self,
    namespace: str = 'garf',
    job_name: str = 'garf_exporter',
    expose_metrics_with_zero_values: bool = False,
  ) -> None:
    """Initializes GarfExporter to serve metrics.

    Args:
      namespace: Global prefix for all Prometheus metrics.
      job_name: Name of export job in Prometheus.
      expose_metrics_with_zero_values: Whether to send zero metrics.
    """
    self.namespace = namespace
    self.job_name = job_name
    self.expose_metrics_with_zero_values = expose_metrics_with_zero_values
    self.registry: prometheus_client.CollectorRegistry = (
      prometheus_client.CollectorRegistry()
    )

  @property
  def export_started(self) -> prometheus_client.Gauge:
    """Gauge for tracking start of collectors export."""
    return self._define_gauge('export_started_seconds', suffix='Remove')

  @property
  def export_completed(self) -> prometheus_client.Gauge:
    """Gauge for tracking end of collectors export."""
    return self._define_gauge('export_completed_seconds', suffix='Remove')

  @property
  def total_export_time_gauge(self) -> prometheus_client.Gauge:
    """Gauge for tracking exports in seconds."""
    return self._define_gauge('exporting_seconds', suffix='Remove')

  @property
  def report_fetcher_gauge(self) -> prometheus_client.Gauge:
    """Gauge for tracking report fetching for account in seconds."""
    return self._define_gauge(
      name='report_fetching_seconds',
      suffix='Remove',
      labelnames=('collector',),
    )

  @property
  def delay_gauge(self) -> prometheus_client.Gauge:
    """Gauge for exposing delay between exports."""
    return self._define_gauge('delay_seconds', suffix='Remove')

  def reset_registry(self) -> None:
    """Removes all metrics from registry before export."""
    self.registry._collector_to_names.clear()
    self.registry._names_to_collectors.clear()

  def export(
    self,
    report: garf_core.GarfReport,
    suffix: str = '',
    collector: str | None = None,
  ) -> None:
    """Exports data from report into the format consumable by Prometheus.

    Iterates over each row or report and creates gauges (metrics with labels
    attached to them) which are added to the registry.

    Args:
      report: Report with API data.
      suffix: Common identifier to be added to a series of metrics.
      collector: Name of one of GarfExporter collectors attached to report.
    """
    if not report:
      return
    start = time.time()
    export_time_gauge = self._define_gauge(
      name='query_export_time_seconds',
      suffix='Remove',
      labelnames=('collector',),
    )
    api_requests_counter = self._define_counter(name='api_requests_count')
    metrics = self._define_metrics(report.query_specification, suffix)
    labels = self._define_labels(report.query_specification)
    for row in report:
      label_values = []
      for label in labels:
        if isinstance(row.get(label), abc.MutableSequence):
          label_value = ','.join([str(r) for r in row.get(label)])
        else:
          label_value = row.get(label)
        label_values.append(label_value)
      for name, metric in metrics.items():
        if (
          metric_value := getattr(row, name)
          or self.expose_metrics_with_zero_values
        ) and not isinstance(metric_value, str):
          metric.labels(*label_values).set(metric_value)
    end = time.time()
    export_time_gauge.labels(collector=collector).set(end - start)
    api_requests_counter.inc()
    self.registry.collect()

  def _define_metrics(
    self,
    query_specification: garf_core.query_editor.QuerySpecification,
    suffix: str,
  ) -> dict[str, prometheus_client.Gauge]:
    """Defines metrics to be exposed Prometheus.

    Metrics are defined based on query_specification of report that needs to
    be exposed. It takes into account both virtual and non-virtual columns.

    Args:
      query_specification:
        QuerySpecification that contains all information about the query.
      suffix: Common identifier to be added to a series of metrics.

    Returns:
      Mapping between metrics alias in report and Gauge.
    """
    metrics = {}
    labels = self._define_labels(query_specification)
    non_virtual_columns = self._get_non_virtual_columns(query_specification)
    for column, field in zip(non_virtual_columns, query_specification.fields):
      if 'metric' in field or 'metric' in column:
        metrics[column] = self._define_gauge(column, suffix, labels)
    if virtual_columns := query_specification.virtual_columns:
      for column, field in virtual_columns.items():
        metrics[column] = self._define_gauge(column, suffix, labels)
    logging.debug('metrics: %s', metrics)
    return metrics

  def _define_labels(
    self, query_specification: garf_core.query_editor.QuerySpecification
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
    for column, field in zip(non_virtual_columns, query_specification.fields):
      if 'metric' not in field and 'metric' not in column:
        labelnames.append(str(column))
    logger.debug('labelnames: %s', labelnames)
    return labelnames

  def _define_gauge(
    self,
    name: str,
    suffix: str,
    labelnames: Sequence[str] = (),
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
      labelnames: Dimensions attached to metric (i.e. ad_group_id, account).

    Returns:
      An instance of Counter that associated with registry.
    """
    if suffix and suffix != 'Remove':
      gauge_name = f'{self.namespace}_{suffix}_{name}'
    else:
      gauge_name = f'{self.namespace}_{name}'
    if gauge_name in self.registry._names_to_collectors:
      return self.registry._names_to_collectors.get(gauge_name)
    return prometheus_client.Gauge(
      name=gauge_name,
      documentation=name,
      labelnames=labelnames,
      registry=self.registry,
    )

  def _define_counter(self, name: str) -> prometheus_client.Counter:
    """Define Counter metric based on provided name.

    Args:
      name: Name of the metric to be exposed to Prometheus (without prefix).

    Returns:
      An instance of Counter that associated with registry.
    """
    counter_name = f'{self.namespace}_{name}'
    if counter_name in self.registry._names_to_collectors:
      return self.registry._names_to_collectors.get(counter_name)
    return prometheus_client.Counter(
      name=counter_name, documentation=name, registry=self.registry
    )

  def _get_non_virtual_columns(
    self, query_specification: garf_core.query_editor.QuerySpecification
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

  def __str__(self) -> str:  # noqa: D105
    return f'GarfExporter(namespace={self.namespace}, job_name={self.job_name})'
