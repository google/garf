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

try:
  from google.cloud import bigquery  # type: ignore
except ImportError as e:
  raise ImportError(
    'Please install garf-executors with BigQuery support '
    '- `pip install garf-executors[bq]`'
  ) from e

import logging

from garf_core import query_editor, report
from google.cloud import exceptions as google_cloud_exceptions

from garf_executors import exceptions, execution_context, executor
from garf_executors.telemetry import tracer

logger = logging.getLogger(__name__)


class BigQueryExecutorError(exceptions.GarfExecutorError):
  """Error when BigQueryExecutor fails to run query."""


class BigQueryExecutor(executor.Executor, query_editor.TemplateProcessorMixin):
  """Handles query execution in BigQuery.

  Attributes:
      project_id: Google Cloud project id.
      location: BigQuery dataset location.
      client: BigQuery client.
  """

  def __init__(
    self,
    project_id: str | None = os.getenv('GOOGLE_CLOUD_PROJECT'),
    location: str | None = None,
  ) -> None:
    """Initializes BigQueryExecutor.

    Args:
        project_id: Google Cloud project id.
        location: BigQuery dataset location.
    """
    if not project_id:
      raise BigQueryExecutorError(
        'project_id is required. Either provide it as project_id parameter '
        'or GOOGLE_CLOUD_PROJECT env variable.'
      )
    self.project_id = project_id
    self.location = location

  @property
  def client(self) -> bigquery.Client:
    """Instantiates bigquery client."""
    return bigquery.Client(self.project_id)

  @tracer.start_as_current_span('bq.execute')
  def execute(
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
    query_text = self.replace_params_template(query, context.query_parameters)
    self.create_datasets(context.query_parameters.macro)
    job = self.client.query(query_text)
    try:
      result = job.result()
      logger.debug('%s launched successfully', title)
      if result.total_rows:
        results = report.GarfReport.from_pandas(result.to_dataframe())
      else:
        results = report.GarfReport()
      if context.writer and results:
        writer_clients = context.writer_clients
        if not writer_clients:
          logger.warning('No writers configured, skipping write operation')
        else:
          writing_results = []
          for writer_client in writer_clients:
            logger.debug(
              'Start writing data for query %s via %s writer',
              title,
              type(writer_client),
            )
            writing_result = writer_client.write(results, title)
            logger.debug(
              'Finish writing data for query %s via %s writer',
              title,
              type(writer_client),
            )
            writing_results.append(writing_result)
          logger.info('%s executed successfully', title)
          # Return the last writer's result for backward compatibility
          return writing_results[-1] if writing_results else None
      return results
    except google_cloud_exceptions.GoogleCloudError as e:
      raise BigQueryExecutorError(e) from e

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
        dataset_id = f'{self.project_id}.{dataset}'
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
