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
from typing import Literal

try:
  import pandas as pd
  import pandas_gbq
  from google.cloud import bigquery
except ImportError as e:
  raise ImportError(
    'Please install garf-io with BigQuery support - `pip install garf-io[bq]`'
  ) from e

import logging

import numpy as np
from garf_core import report as garf_report
from google.cloud import exceptions as google_cloud_exceptions

from garf_io import exceptions, formatter
from garf_io.writers import abs_writer

logger = logging.getLogger(__name__)

_WRITE_DISPOSITION_MAPPING = {
  'WRITE_TRUNCATE': 'replace',
  'WRITE_TRUNCATE_DATA': 'replace',
  'WRITE_APPEND': 'append',
  'WRITE_EMPTY': 'fail',
}


class BigQueryWriterError(exceptions.GarfIoError):
  """BigQueryWriter specific errors."""


class BigQueryWriter(abs_writer.AbsWriter):
  """Writes Garf Report to BigQuery.

  Attributes:
    project: Id of Google Cloud Project.
    dataset: BigQuery dataset to write data to.
    location: Location of a newly created dataset.
    write_disposition: Option for overwriting data.
  """

  def __init__(
    self,
    project: str | None = os.getenv('GOOGLE_CLOUD_PROJECT'),
    dataset: str = 'garf',
    location: str = 'US',
    write_disposition: bigquery.WriteDisposition
    | Literal['append', 'replace', 'fail'] = 'replace',
    **kwargs,
  ):
    """Initializes BigQueryWriter.

    Args:
      project: Id of Google Cloud Project.
      dataset: BigQuery dataset to write data to.
      location: Location of a newly created dataset.
      write_disposition: Option for overwriting data.
      kwargs: Optional keywords arguments.
    """
    super().__init__(**kwargs)
    if not project:
      raise BigQueryWriterError(
        'project is required. Either provide it as project parameter '
        'or GOOGLE_CLOUD_PROJECT env variable.'
      )
    self.project = project
    self.dataset_id = f'{project}.{dataset}'
    self.location = location
    if write_disposition in ('replace', 'append', 'fail'):
      self.write_disposition = write_disposition
    elif isinstance(write_disposition, bigquery.WriteDisposition):
      self.write_disposition = _WRITE_DISPOSITION_MAPPING.get(
        write_disposition.name
      )
    elif _WRITE_DISPOSITION_MAPPING.get(write_disposition.upper()):
      self.write_disposition = _WRITE_DISPOSITION_MAPPING.get(
        write_disposition.upper()
      )
    else:
      raise BigQueryWriterError(
        'Unsupported writer disposition, choose one of: replace, append, fail'
      )

  def __str__(self) -> str:
    return f'[BigQuery] - {self.dataset_id} at {self.location} location.'

  @property
  def client(self) -> bigquery.Client:
    """Instantiated BigQuery client."""
    return bigquery.Client(self.project)

  def create_or_get_dataset(self) -> bigquery.Dataset:
    """Gets existing dataset or create a new one."""
    try:
      bq_dataset = self.client.get_dataset(self.dataset_id)
    except google_cloud_exceptions.NotFound:
      bq_dataset = bigquery.Dataset(self.dataset_id)
      bq_dataset.location = self.location
      bq_dataset = self.client.create_dataset(bq_dataset, timeout=30)
    return bq_dataset

  def write(self, report: garf_report.GarfReport, destination: str) -> str:
    """Writes Garf report to a BigQuery table.

    Args:
      report: Garf report.
      destination: Name of the table report should be written to.

    Returns:
      Name of the table in `dataset.table` format.
    """
    report = self.format_for_write(report)
    destination = formatter.format_extension(destination)
    _ = self.create_or_get_dataset()
    table = f'{self.dataset_id}.{destination}'
    if not report:
      df = pd.DataFrame(
        data=report.results_placeholder, columns=report.column_names
      ).head(0)
    else:
      df = report.to_pandas()
    df = df.replace({np.nan: None})
    logger.debug('Writing %d rows of data to %s', len(df), destination)
    pandas_gbq.to_gbq(
      dataframe=df, destination_table=table, if_exists=self.write_disposition
    )
    logger.debug('Writing to %s is completed', destination)
    return f'[BigQuery] - at {self.dataset_id}.{destination}'
