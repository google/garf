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
"""Runs garf workflow."""

from __future__ import annotations

import logging
import pathlib
import re
from typing import Final

import yaml
from garf.executors import exceptions, setup
from garf.executors.telemetry import tracer
from garf.executors.workflows import workflow
from garf.io import reader

logger = logging.getLogger(__name__)

_REMOTE_FILES_PATTERN: Final[str] = (
  '^(http|gs|s3|aruze|hdfs|webhdfs|ssh|scp|sftp)'
)
_SCRIPT_PATH = pathlib.Path(__file__).parent


class WorkflowRunner:
  """Runs garf workflow.

  Attributes:
    workflow: Workflow to execute.
    wf_parent: Optional location of a workflow file.
    parallel_threshold: Max allowed parallelism for the queries in the workflow.
  """

  def __init__(
    self,
    execution_workflow: workflow.Workflow,
    wf_parent: pathlib.Path | str,
    parallel_threshold: int = 10,
  ) -> None:
    """Initializes WorkflowRunner."""
    self.workflow = execution_workflow
    self.wf_parent = wf_parent
    self.parallel_threshold = parallel_threshold

  @classmethod
  def from_file(cls, workflow_file: str | pathlib.Path) -> WorkflowRunner:
    """Initialized Workflow runner from a local or remote file."""
    if isinstance(workflow_file, str):
      workflow_file = pathlib.Path(workflow_file)
    execution_workflow = workflow.Workflow.from_file(workflow_file)
    return cls(
      execution_workflow=execution_workflow, wf_parent=workflow_file.parent
    )

  def run(
    self, enable_cache: bool = False, cache_ttl_seconds: int = 3600
  ) -> list[str]:
    reader_client = reader.create_reader('file')
    execution_results = []
    logger.info('Starting Garf Workflow...')
    for i, step in enumerate(self.workflow.steps, 1):
      step_name = f'{i}-{step.fetcher}'
      if step.alias:
        step_name = f'{step_name}-{step.alias}'
      with tracer.start_as_current_span(step_name):
        logger.info(
          'Running step %d, fetcher: %s, alias: %s', i, step.fetcher, step.alias
        )
        query_executor = setup.setup_executor(
          source=step.fetcher,
          fetcher_parameters=step.fetcher_parameters,
          enable_cache=enable_cache,
          cache_ttl_seconds=cache_ttl_seconds,
        )
        batch = {}
        if not (queries := step.queries):
          logger.error('Please provide one or more queries to run')
          raise exceptions.GarfExecutorError(
            'Please provide one or more queries to run'
          )
        for query in queries:
          if isinstance(query, workflow.QueryPath):
            query_path = query.full_path
            if re.match(_REMOTE_FILES_PATTERN, query_path):
              batch[query.path] = reader_client.read(query_path)
            else:
              if not query.prefix:
                query_path = self.wf_parent / pathlib.Path(query.path)
              if not query_path.exists():
                raise workflow.GarfWorkflowError(
                  f'Query: {query_path} not found'
                )
              batch[query.path] = reader_client.read(query_path)
          elif isinstance(query, workflow.QueryFolder):
            query_path = self.wf_parent / pathlib.Path(query.folder)
            if not query_path.exists():
              raise workflow.GarfWorkflowError(
                f'Folder: {query_path} not found'
              )
            for p in query_path.rglob('*'):
              if p.suffix == '.sql':
                batch[p.stem] = reader_client.read(p)
          else:
            batch[query.query.title] = query.query.text
        query_executor.execute_batch(
          batch, step.context, self.parallel_threshold
        )
        execution_results.append(step_name)
    return execution_results

  def compile(self, path: str | pathlib.Path) -> str:
    """Saves workflow with expanded anchors."""
    return self.workflow.save(path)

  def deploy(self, path: str | pathlib.Path) -> str:
    """Prepares workflow for deployment to Google Cloud Workflows."""
    wf = self.workflow.model_dump(exclude_none=True).get('steps')
    with open(_SCRIPT_PATH / 'gcp_workflow.yaml', 'r', encoding='utf-8') as f:
      cloud_workflow_run_template = yaml.safe_load(f)
    init = {
      'init': {
        'assign': [{'pairs': wf}],
      },
    }
    cloud_workflow = {
      'main': {
        'params': [],
        'steps': [init, cloud_workflow_run_template],
      },
    }
    with open(path, 'w', encoding='utf-8') as f:
      yaml.dump(cloud_workflow, f, sort_keys=False)
    return f'Workflow is saved to {path}'
