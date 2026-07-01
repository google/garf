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
"""Writes GarfReport to BigQuery."""

from __future__ import annotations

import os

try:
  import pandas as pd
  import pandas_gbq
  from google.cloud import bigquery
except ImportError as e:
  raise ImportError(
    'Please install garf-io with BigQuery support - `pip install garf-io[bq]`'
  ) from e

import contextlib
import logging

import numpy as np
import pydantic
from garf.core import report as garf_report
from garf.io import exceptions, formatter
from garf.io.telemetry import tracer
from garf.io.writers import abs_writer
from google.cloud import exceptions as google_cloud_exceptions
from opentelemetry import trace

logger = logging.getLogger(__name__)
logging.getLogger('pandas_gbq').setLevel(logging.WARNING)

_WRITE_DISPOSITION_MAPPING = {
  'WRITE_TRUNCATE': 'replace',
  'WRITE_TRUNCATE_DATA': 'replace',
  'WRITE_APPEND': 'append',
  'WRITE_EMPTY': 'fail',
}


class BigQueryWriterError(exceptions.GarfIoError):
  """BigQueryWriter specific errors."""


class BigQueryWriterOptions(abs_writer.WriterOptions):
  """Options for writing report to BigQuery.

  Attributes:
    project: Id of Google Cloud Project.
    dataset: BigQuery dataset to write data to.
    location: Location of a newly created dataset.
    write_disposition: Option for overwriting data.
    time_partitioning_column: Column to partition tables by date.
    time_partitioning_type: Type of time partitioning (DAY, HOUR, MONTH, YEAR).
    time_partitioning_expiration_ms:
      Expiration of time partitioned tables in milliseconds.
    range_partitioning_column: Column to partition tables into ranges.
    range_partitioning_range: Range definition in start:end:interval format.
    clustering_columns: Column(s) to perform clustering of table.
    default_table_expiration_ms:
      Expiration of tables in the dataset in milliseconds.
    skip_dataset_creation: Whether to proceed without creating dataset.
  """

  model_config = pydantic.ConfigDict(
    extra='allow', arbitrary_types_allowed=True
  )

  project: str = os.getenv('GOOGLE_CLOUD_PROJECT')
  dataset: str = 'garf'
  location: str = 'US'
  write_disposition: bigquery.WriteDisposition | str = 'replace'
  time_partitioning_column: str | None = None
  time_partitioning_type: str | None = None
  time_partitioning_expiration_ms: int | None = None
  range_partitioning_column: str | None = None
  range_partitioning_range: str | None = None
  clustering_columns: str | list[str] | None = None
  default_table_expiration_ms: int | None = None
  skip_dataset_creation: bool = False

  def model_post_init(self, __context) -> None:
    if isinstance(self.write_disposition, bigquery.WriteDisposition):
      self.write_disposition = _WRITE_DISPOSITION_MAPPING.get(
        self.write_disposition.name
      )
    elif _WRITE_DISPOSITION_MAPPING.get(self.write_disposition.upper()):
      self.write_disposition = _WRITE_DISPOSITION_MAPPING.get(
        self.write_disposition.upper()
      )
    elif self.write_disposition not in (_WRITE_DISPOSITION_MAPPING.values()):
      raise BigQueryWriterError(
        'Unsupported writer disposition, choose one of: replace, append, fail'
      )
    if self.time_partitioning_column:
      if not self.time_partitioning_type:
        self.time_partitioning_type = 'DAY'
      elif self.time_partitioning_type not in (
        'DAY',
        'HOUR',
        'MONTH',
        'YEAR',
      ):
        raise BigQueryWriterError(
          'Unsupported time_partitioning type, '
          'choose one of: DAY, HOUR, MONTH, YEAR'
        )
    if self.range_partitioning_range:
      try:
        start, end, interval = self.range_partitioning_range.split(':')
        self.range_partitioning_range = {
          'start': int(start),
          'end': int(end),
          'interval': int(interval),
        }
      except ValueError as e:
        raise BigQueryWriterError(
          'Unsupported range_partitioning_range, '
          'specify in start:end:interval format'
        ) from e

    else:
      self.range_partitioning_range = None
    if self.clustering_columns:
      self.clustering_columns = self.clustering_columns.split(',')
    else:
      self.clustering_columns = None

  @property
  def dataset_id(self) -> str:
    return f'{self.project}.{self.dataset}'


class BigQueryWriter(abs_writer.AbsWriter):
  """Writes Garf Report to BigQuery."""

  def __init__(
    self,
    options: BigQueryWriterOptions | None = None,
    **kwargs,
  ):
    """Initializes BigQueryWriter."""
    super().__init__(**kwargs)
    self.options = options if options else BigQueryWriterOptions(**kwargs)
    self._client = None

  def __str__(self) -> str:
    return f'[BigQuery] - {self.options.dataset_id} at {self.options.location} location.'

  @property
  def client(self) -> bigquery.Client:
    """Instantiated BigQuery client."""
    if not self._client:
      with tracer.start_as_current_span('bq.create_client'):
        self._client = bigquery.Client(self.options.project)
    return self._client

  @tracer.start_as_current_span('bq.create_or_get_dataset')
  def create_or_get_dataset(self) -> bigquery.Dataset:
    """Gets existing dataset or create a new one."""
    if self.options.skip_dataset_creation:
      return bigquery.Dataset(self.options.dataset_id)
    try:
      bq_dataset = self.client.get_dataset(self.options.dataset_id)
    except google_cloud_exceptions.NotFound:
      bq_dataset = bigquery.Dataset(self.options.dataset_id)
      if table_expiration := self.options.default_table_expiration_ms:
        bq_dataset.default_table_expiration_ms = int(table_expiration)
      bq_dataset.location = self.options.location
      with contextlib.suppress(google_cloud_exceptions.Conflict):
        bq_dataset = self.client.create_dataset(bq_dataset, timeout=30)
        logger.info('Created new dataset %s', self.options.dataset_id)
    return bq_dataset

  @tracer.start_as_current_span('bq.write')
  def write(self, report: garf_report.GarfReport, destination: str) -> str:
    """Writes Garf report to a BigQuery table.

    Args:
      report: Garf report.
      destination: Name of the table report should be written to.

    Returns:
      Name of the table in `dataset.table` format.
    """
    span = trace.get_current_span()
    report = self.format_for_write(report)
    destination = formatter.format_extension(
      destination, prefix=self.options.prefix, suffix=self.options.suffix
    )
    table = f'{self.options.dataset_id}.{destination}'
    if not report:
      df = pd.DataFrame(
        data=report.results_placeholder, columns=report.column_names
      ).head(0)
      span.set_attribute('is_placeholder_report', True)
    else:
      df = report.to_pandas()
    df = df.replace({np.nan: None})
    logger.debug('Writing %d rows of data to %s', len(df), destination)
    pandas_gbq.to_gbq(
      dataframe=df,
      project_id=self.options.project,
      destination_table=table,
      if_exists=self.options.write_disposition,
      progress_bar=False,
      time_partitioning_column=self.options.time_partitioning_column,
      time_partitioning_type=self.options.time_partitioning_type,
      time_partitioning_expiration_ms=self.options.time_partitioning_expiration_ms,
      range_partitioning_column=self.options.range_partitioning_column,
      range_partitioning_range=self.options.range_partitioning_range,
      clustering_columns=self.options.clustering_columns,
    )
    logger.debug('Writing to %s is completed', destination)
    return f'[BigQuery] - at {self.options.dataset_id}.{destination}'
