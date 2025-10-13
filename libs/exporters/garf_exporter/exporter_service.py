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

"""Handles exporting all metrics based on a request."""

from __future__ import annotations

import logging
import os
from time import time
from typing import Literal, Optional, Union

import garf_core
import pydantic
from garf_executors import fetchers

import garf_exporter
from garf_exporter import collector

logger = logging.getLogger(__name__)


class GarfExporterRuntimeOptions(pydantic.BaseModel):
  """Options to finetune exporting process.

  Attributes:
    expose_type: Type of exposition (http or pushgateway).
    host: Address of expose endpoint.
    port: Port of expose endpoint.
    iterations: Optional number of iterations to perform.
    delay_minutes: Delay between exports.
    namespace: Prefix for all metrics exposed to Prometheus.
    job_name: Job name attached to each metric.
    fetching_timeout:
      Period to abort fetching if not data from API returned.
    max_workers: Maximum number of parallel fetching from an API.
  """

  host: str = '0.0.0.0'
  port: int = 8000
  expose_type: Literal['http', 'pushgateway'] = 'http'
  iterations: Optional[int] = None
  delay_minutes: int = 15
  namespace: str = 'garf'
  job_name: str = 'garf_exporter'
  fetching_timeout: int = 120
  max_workers: Optional[int] = None

  @property
  def address(self) -> str:
    return f'{self.host}:{self.port}'


class GarfExporterRequest(pydantic.BaseModel):
  """Request to API to perform export to Prometheus.

  Attributes:
    source: Type of API to get data from.
    source_parameters: Optional parameters to configure the API connection.
    collectors_config: Path to YAML file with collector definitions.
    query_parameters: Optional parameters to refine queries in collectors.
    runtime_options: Options to finetune exporting process.
  """

  source: str
  source_parameters: dict[str, Union[str, int]] = pydantic.Field(
    default_factory=dict
  )
  collectors_config: Union[os.PathLike[str], str, None] = None
  query_parameters: Optional[garf_core.query_editor.GarfQueryParameters] = None
  runtime_options: GarfExporterRuntimeOptions = GarfExporterRuntimeOptions()
  collectors: list[collector.Collector] = pydantic.Field(default_factory=list)


class GarfExporterService:
  """Responsible for getting data from API and exposing it to Prometheus.

  Attributes:
    alias: Type of fetcher used to get data from an API.
    fetcher: Initialized ApiReportFetcher to perform fetching from an API.
  """

  def __init__(
    self,
    alias: str,
    source_parameters: Optional[dict[str, Union[str, int]]] = None,
  ) -> None:
    """Initializes GarfExporterService."""
    self.alias = alias
    self.source_parameters = source_parameters or {}
    self._report_fetcher = None

  @property
  def fetcher(self) -> garf_core.ApiReportFetcher:
    """Initialized ApiReportFetcher for fetching data from an API."""
    if self._report_fetcher:
      return self._report_fetcher
    fetcher = fetchers.get_report_fetcher(self.alias)
    self._report_fetcher = fetcher(**self.source_parameters)
    return self._report_fetcher

  def generate_metrics(
    self,
    request: GarfExporterRequest,
    exporter: garf_exporter.GarfExporter,
  ) -> None:
    """Generates metrics based on API request.

    Args:
      request: Complete request to fetch and expose data.
      exporter: Initialized GarfExporter.
    """
    logger.info('Beginning export')
    start_export_time = time()
    exporter.export_started.set(start_export_time)
    collectors = request.collectors or collector.load_collector_data(
      request.collectors_config
    )
    for col in collectors:
      logger.info('Exporting from collector: %s', col.title)
      start = time()
      report = self.fetcher.fetch(
        col.query, args=request.query_parameters, **self.source_parameters
      )
      end = time()
      exporter.report_fetcher_gauge.labels(collector=col.title).set(end - start)
      exporter.export(
        report=report,
        suffix=col.suffix,
        collector=col.title,
      )
    logger.info('Export completed')
    end_export_time = time()
    exporter.export_completed.set(end_export_time)
    exporter.total_export_time_gauge.set(end_export_time - start_export_time)
    exporter.delay_gauge.set(request.runtime_options.delay_minutes * 60)
