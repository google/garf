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
import time

import yaml
from garf.executors import exceptions, setup, telemetry
from garf.executors.telemetry import tracer
from garf.executors.workflows import workflow
from opentelemetry import trace

logger = logging.getLogger(__name__)

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
    wf_parent: pathlib.Path | str | None = None,
    parallel_threshold: int = 10,
  ) -> None:
    """Initializes WorkflowRunner."""
    self.workflow = execution_workflow
    self.wf_parent = wf_parent
    self.parallel_threshold = parallel_threshold

  @classmethod
  def from_file(
    cls,
    workflow_file: str | pathlib.Path,
  ) -> WorkflowRunner:
    """Initialized Workflow runner from a local or remote file."""
    if isinstance(workflow_file, str):
      workflow_file = pathlib.Path(workflow_file)
    execution_workflow = workflow.Workflow.from_file(workflow_file)
    return cls(
      execution_workflow=execution_workflow, wf_parent=workflow_file.parent
    )

  @tracer.start_as_current_span('workflow.run')
  def run(
    self,
    enable_cache: bool = False,
    cache_ttl_seconds: int = 3600,
    selected_aliases: list[str] | None = None,
    skipped_aliases: list[str] | None = None,
    simulate: bool = False,
  ) -> list[str]:
    span = trace.get_current_span()
    start_time = time.perf_counter()
    workflow_attributes = {}
    if name := self.workflow.name:
      workflow_attributes.update({'workflow.name': name})
    if version := self.workflow.metadata.version:
      workflow_attributes.update({'workflow.version': version})
    if config := self.workflow.execution_config:
      if config_version := config.metadata.version:
        workflow_attributes.update({'config.version': config_version})
      if config_name := config.name:
        workflow_attributes.update({'config.name': config_name})

    steps = [step.fetcher for step in self.workflow.steps]
    workflow_attributes.update(
      {
        'workflow.num_steps': len(steps),
        'workflow.fetchers': list(set(steps)),
      }
    )
    span.set_attributes(workflow_attributes)
    self.workflow.compile()
    skipped_aliases = skipped_aliases or []
    selected_aliases = selected_aliases or []
    execution_results = {}
    logger.info('Starting Garf Workflow...')
    for i, step in enumerate(self.workflow.steps, 1):
      step_name = f'{i}-{step.fetcher}'

      if step.alias:
        step_name = f'{step_name}-{step.alias}'
      if step.alias in skipped_aliases:
        logger.warning(
          'Skipping step %d, fetcher: %s, alias: %s',
          i,
          step.fetcher,
          step.alias,
        )
        continue
      if selected_aliases and step.alias not in selected_aliases:
        logger.warning(
          'Skipping step %d, fetcher: %s, alias: %s',
          i,
          step.fetcher,
          step.alias,
        )
        continue
      workflow_step_attributes = {
        **workflow_attributes,
        'workflow.step.name': step_name,
      }
      with tracer.start_as_current_span(step_name) as step_span:
        logger.info(
          'Running step %d, fetcher: %s, alias: %s', i, step.fetcher, step.alias
        )
        step_attributes = {
          'step.alias': step.alias,
          'step.fetcher': step.fetcher,
        }
        if step.writer:
          step_attributes.update({'step.writer': step.writer})

        step_span.set_attributes(step_attributes)

        query_executor = setup.setup_executor(
          source=step.fetcher,
          fetcher_parameters=step.fetcher_parameters,
          enable_cache=enable_cache,
          cache_ttl_seconds=cache_ttl_seconds,
          simulate=simulate,
          writers=step.writer,
          writer_parameters=step.writer_parameters,
        )
        if fetcher_version := self.workflow.metadata.required_fetchers.get(
          step.fetcher
        ):
          _validate_fetcher_version(
            version=fetcher_version,
            target_version=query_executor.fetcher.version,
            fetcher_name=step.fetcher,
          )

        batch = {}
        if not (queries := step.queries):
          logger.error('Please provide one or more queries to run')
          raise exceptions.GarfExecutorError(
            'Please provide one or more queries to run'
          )
        for query in queries:
          if isinstance(query, workflow.QueryFolder):
            for q in query.queries:
              batch[q.title] = q.text
          else:
            batch[query.title] = query.text
        try:
          step_start_time = time.perf_counter()
          step_span.set_attribute('step.num_queries', len(batch))
          results = query_executor.execute_batch(
            batch,
            step.context,
            step.parallel_threshold or self.parallel_threshold,
          )
          execution_results[step_name] = results
          telemetry.workflow_step_counter.add(1, workflow_step_attributes)
          step_duration = time.perf_counter() - step_start_time
          telemetry.workflow_step_histogram.record(
            step_duration, workflow_step_attributes
          )
        except exceptions.GarfExecutorError as e:
          telemetry.workflow_step_error_counter.add(1, workflow_step_attributes)
          telemetry.workflow_error_counter.add(1, workflow_attributes)
          raise e
    logger.info('Garf Workflow completed.')
    telemetry.workflow_counter.add(1, workflow_attributes)
    duration = time.perf_counter() - start_time
    telemetry.workflow_histogram.record(duration, workflow_attributes)
    return execution_results

  def compile(self, path: str | pathlib.Path) -> str:
    """Saves workflow with expanded anchors."""
    self.workflow.compile()
    return self.workflow.save(path)

  def deploy(
    self, path: str | pathlib.Path, embed_queries: bool = False
  ) -> str:
    """Prepares workflow for deployment to Google Cloud Workflows."""
    if embed_queries:
      self.workflow.compile()
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


def _validate_fetcher_version(
  version: str, target_version: str, fetcher_name: str
):
  library_version = tuple(map(int, target_version.split('.')))
  checked_version = tuple(map(int, version.split('.')))
  if library_version < checked_version:
    raise exceptions.GarfExecutorError(
      f'Garf version for {fetcher_name} ({target_version}) is below required '
      f'by workflow - {version}.'
    )
  return True
