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
"""Workflow specifies steps of end-to-end fetching and processing."""

from __future__ import annotations

import copy
import os
import pathlib
import re
from collections import defaultdict
from typing import Any

import pydantic
import smart_open
import yaml
from garf.executors import exceptions
from garf.executors.execution_context import ExecutionContext


class GarfWorkflowError(exceptions.GarfExecutorError):
  """Workflow specific exception."""


class QueryFolder(pydantic.BaseModel):
  """Path to folder with queries."""

  folder: str


class QueryPath(pydantic.BaseModel):
  """Path file with query."""

  path: str
  prefix: str | None = None

  @property
  def full_path(self) -> str:
    if self.prefix:
      return re.sub('/$', '', self.prefix) + '/' + self.path
    return self.path


class QueryDefinition(pydantic.BaseModel):
  """Definition of a query."""

  query: Query


class Query(pydantic.BaseModel):
  """Query elements.

  Attributes:
    text: Query text.
    title: Name of the query.
  """

  text: str
  title: str


class ExecutionStep(ExecutionContext):
  """Common context for executing one or more queries.

  Attributes:
    fetcher: Name of a fetcher to get data from API.
    alias: Optional alias to identify execution step.
    queries: Queries to run for a particular fetcher.
    context: Execution context for queries and fetcher.
    parallel_threshold: Max allowed parallelism for the queries in the step.
  """

  fetcher: str | None = None
  alias: str | None = pydantic.Field(default=None, pattern=r'^[a-zA-Z0-9_]+$')
  queries: list[QueryPath | QueryDefinition | QueryFolder] | None = None
  parallel_threshold: int | None = None

  @property
  def context(self) -> ExecutionContext:
    return ExecutionContext(
      writer=self.writer,
      writer_parameters=self.writer_parameters,
      query_parameters=self.query_parameters,
      fetcher_parameters=self.fetcher_parameters,
    )


class Workflow(pydantic.BaseModel):
  """Orchestrates execution of queries for multiple fetchers.

  Attributes:
    steps: Contains one or several fetcher executions.
    context: Query and fetcher parameters to overwrite in steps.
  """

  steps: list[ExecutionStep]
  context: ExecutionContext | None = None

  def model_post_init(self, __context__) -> None:
    if context := self.context:
      custom_parameters = defaultdict(dict)
      if custom_macros := context.query_parameters.macro:
        custom_parameters['query_parameters']['macro'] = custom_macros
      if custom_templates := context.query_parameters.template:
        custom_parameters['query_parameters']['template'] = custom_templates
      if custom_fetcher_parameters := context.fetcher_parameters:
        custom_parameters['fetcher_parameters'] = custom_fetcher_parameters
      if custom_writer_parameters := context.writer_parameters:
        custom_parameters['writer_parameters'] = custom_writer_parameters

      if custom_parameters:
        steps = self.steps
        for i, step in enumerate(steps):
          res = _merge_dicts(
            step.model_dump(exclude_none=True), dict(custom_parameters)
          )
          steps[i] = ExecutionStep(**res)

  @classmethod
  def from_file(
    cls,
    path: str | pathlib.Path | os.PathLike[str],
    context: ExecutionContext | None = None,
  ) -> Workflow:
    """Builds workflow from local or remote yaml file."""
    with smart_open.open(path, 'r', encoding='utf-8') as f:
      data = yaml.safe_load(f)
    try:
      return Workflow(steps=data.get('steps'), context=context)
    except pydantic.ValidationError as e:
      raise GarfWorkflowError(f'Incorrect workflow:\n {e}') from e

  def save(self, path: str | pathlib.Path | os.PathLike[str]) -> str:
    """Saves workflow to local or remote yaml file."""
    with smart_open.open(path, 'w', encoding='utf-8') as f:
      yaml.dump(
        self.model_dump(exclude_none=True), f, encoding='utf-8', sort_keys=False
      )
    return f'Workflow is saved to {str(path)}'


def _merge_dicts(
  dict1: dict[str, Any], dict2: dict[str, Any]
) -> dict[str, Any]:
  result = copy.deepcopy(dict1)
  for key, value in dict2.items():
    if (
      key in result
      and isinstance(result[key], dict)
      and isinstance(value, dict)
    ):
      result[key] = _merge_dicts(result[key], value)
    else:
      result[key] = value
  return result
