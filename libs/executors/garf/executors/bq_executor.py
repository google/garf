# Copyright 2024 Google LLC
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
"""Executes queries in BigQuery."""

from __future__ import annotations

import contextlib
import os
import warnings

try:
  from google.cloud import bigquery  # type: ignore
except ImportError as e:
  raise ImportError(
    'Please install garf-executors with BigQuery support '
    '- `pip install garf-executors[bq]`'
  ) from e

import logging

from garf.core import report
from garf.executors import exceptions, execution_context, executor
from garf.executors.telemetry import tracer
from garf.io.writers import abs_writer
from google.cloud import exceptions as google_cloud_exceptions

logger = logging.getLogger(__name__)


class BigQueryExecutorError(exceptions.GarfExecutorError):
  """Error when BigQueryExecutor fails to run query."""


class BigQueryExecutor(executor.Executor):
  """Handles query execution in BigQuery.

  Attributes:
    project_id: Google Cloud project id.
    location: BigQuery dataset location.
    client: BigQuery client.
  """

  def __init__(
    self,
    project: str | None = os.getenv('GOOGLE_CLOUD_PROJECT'),
    location: str | None = None,
    writers: list[abs_writer.AbsWriter] | None = None,
    **kwargs: str,
  ) -> None:
    """Initializes BigQueryExecutor.

    Args:
      project_id: Google Cloud project id.
      location: BigQuery dataset location.
      writers: Instantiated writers.
    """
    if not project and 'project_id' not in kwargs:
      raise BigQueryExecutorError(
        'project is required. Either provide it as project parameter '
        'or GOOGLE_CLOUD_PROJECT env variable.'
      )
    if project_id := kwargs.get('project_id'):
      warnings.warn(
        "'project_id' parameter is deprecated. Please use 'project' instead.",
        DeprecationWarning,
        stacklevel=2,
      )
    self.project = project or project_id
    self.location = location
    self.writers = writers
    self._client = None
    super().__init__()

  @property
  def client(self) -> bigquery.Client:
    """Instantiated BigQuery client."""
    if not self._client:
      with tracer.start_as_current_span('bq.create_client'):
        self._client = bigquery.Client(self.project)
    return self._client

  @property
  def project_id(self) -> str:
    warnings.warn(
      "'project_id' property is deprecated. Please use 'project' instead.",
      DeprecationWarning,
      stacklevel=2,
    )
    return self.project

  @tracer.start_as_current_span('bq.execute')
  def _execute(
    self,
    query: str,
    title: str,
    context: execution_context.ExecutionContext = (
      execution_context.ExecutionContext()
    ),
  ) -> report.GarfReport:
    """Executes query in BigQuery.

    Args:
      query: Location of the query.
      title: Name of the query.
      context: Query execution context.

    Returns:
      Report with data if query returns some data otherwise empty Report.
    """
    # TODO: move to initialization
    self.create_datasets(context.query_parameters.macro)
    job = self.client.query(query)
    try:
      result = job.result()
    except google_cloud_exceptions.GoogleCloudError as e:
      raise BigQueryExecutorError(
        f'Failed to execute query {title}: Reason: {e}'
      ) from e
      logger.debug('%s launched successfully', title)
    if result.total_rows:
      return report.GarfReport.from_pandas(result.to_dataframe())
    return report.GarfReport()

  @tracer.start_as_current_span('bq.create_datasets')
  def create_datasets(self, macros: dict | None) -> None:
    """Creates datasets in BQ based on values in a dict.

    If dict contains keys with 'dataset' in them, then values for such keys
    are treated as dataset names.

    Args:
      macros: Mapping containing data for query execution.
    """
    if macros and (datasets := extract_datasets(macros)):
      for dataset in datasets:
        dataset_id = f'{self.project}.{dataset}'
        try:
          self.client.get_dataset(dataset_id)
        except google_cloud_exceptions.NotFound:
          bq_dataset = bigquery.Dataset(dataset_id)
          bq_dataset.location = self.location
          with contextlib.suppress(google_cloud_exceptions.Conflict):
            self.client.create_dataset(bq_dataset, timeout=30)
            logger.info('Created new dataset %s', dataset_id)


def extract_datasets(macros: dict | None) -> list[str]:
  """Finds dataset-related keys based on values in a dict.

  If dict contains keys with 'dataset' in them, then values for such keys
  are treated as dataset names.

  Args:
      macros: Mapping containing data for query execution.

  Returns:
      Possible names of datasets.
  """
  if not macros:
    return []
  return [value for macro, value in macros.items() if 'dataset' in macro]
