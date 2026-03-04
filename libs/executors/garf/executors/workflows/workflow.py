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
from collections import defaultdict
from typing import Any

import pydantic
import smart_open
import yaml
from garf.core import query_editor
from garf.executors import exceptions
from garf.executors.execution_context import ExecutionContext
from garf.io import reader

reader_client = reader.create_reader('file')


class GarfWorkflowError(exceptions.GarfExecutorError):
  """Workflow specific exception."""


class QueryFolder(pydantic.BaseModel):
  """Path to folder with queries."""

  folder: str
  prefix: str | pathlib.Path | None = None

  def model_post_init(self, __context__) -> None:
    if self.prefix:
      self.prefix = pathlib.Path(self.prefix)

  @property
  def queries(self) -> list[QueryPath]:
    batch = []
    query_path = (
      self.prefix / pathlib.Path(self.folder)
      if self.prefix
      else pathlib.Path(self.folder)
    )
    if not query_path.exists():
      raise GarfWorkflowError(f'Folder: {query_path} not found')
    for p in query_path.rglob('*'):
      if p.suffix == '.sql':
        batch.append(QueryPath(path=str(p.name), prefix=str(query_path)))
    return batch


class QueryPath(pydantic.BaseModel):
  """Path file with query."""

  path: str
  prefix: str | pathlib.Path | None = None

  def model_post_init(self, __context__) -> None:
    if self.prefix:
      self.prefix = pathlib.Path(self.prefix)

  @property
  def full_path(self) -> str:
    if self.prefix:
      return self.prefix / self.path
    return self.path

  @property
  def text(self) -> str:
    return reader_client.read(self.full_path)

  @property
  def title(self) -> str:
    return self.path

  def to_query(self, prefix: str | pathlib.Path | None) -> Query:
    if not self.prefix and prefix:
      self.prefix = prefix
    query_spec = query_editor.QuerySpecification(
      text=self.text, title=self.title
    ).remove_comments()
    return Query(title=self.title, text=query_spec.query.text.strip())


class QueryDefinition(pydantic.BaseModel):
  """Definition of a query."""

  query: Query

  @property
  def text(self) -> str:
    return self.query.text

  @property
  def title(self) -> str:
    return self.query.title

  def to_query(self, prefix: str | pathlib.Path | None) -> Query:
    query_spec = query_editor.QuerySpecification(
      text=self.text, title=self.title
    ).remove_comments()
    return Query(title=self.title, text=query_spec.query.text.strip())


class Query(pydantic.BaseModel):
  """Query elements.

  Attributes:
    text: Query text.
    title: Name of the query.
  """

  text: str
  title: str

  def to_query(self, prefix):
    return self


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
  queries: list[Query | QueryPath | QueryDefinition | QueryFolder] | None = None
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
  context: dict[str, dict[str, Any]] | None = None
  prefix: str | pathlib.Path | None = pydantic.Field(
    default=None, excluded=True
  )

  def model_post_init(self, __context__) -> None:
    if context := self.context:
      custom_parameters = defaultdict(dict)
      if custom_macros := context.get('macro'):
        custom_parameters['query_parameters']['macro'] = custom_macros
      if custom_templates := context.get('template'):
        custom_parameters['query_parameters']['template'] = custom_templates

      steps = self.steps
      for i, step in enumerate(steps):
        if fetcher_parameters := context.get(step.fetcher):
          custom_parameters['fetcher_parameters'] = fetcher_parameters
        if writer_parameters := context.get(step.writer):
          custom_parameters['writer_parameters'] = writer_parameters

        res = _merge_dicts(
          step.model_dump(exclude_none=True), custom_parameters
        )
        steps[i] = ExecutionStep(**res)

  @classmethod
  def from_file(
    cls,
    path: str | pathlib.Path | os.PathLike[str],
    context: dict[str, dict[str, Any]] | None = None,
  ) -> Workflow:
    """Builds workflow from local or remote yaml file."""
    with smart_open.open(path, 'r', encoding='utf-8') as f:
      data = yaml.safe_load(f)
    try:
      if isinstance(path, str):
        path = pathlib.Path(path)
      return Workflow(
        steps=data.get('steps'), context=context, prefix=path.parent
      )
    except pydantic.ValidationError as e:
      raise GarfWorkflowError(f'Incorrect workflow:\n {e}') from e

  def save(self, path: str | pathlib.Path | os.PathLike[str]) -> str:
    """Saves workflow to local or remote yaml file."""
    with smart_open.open(path, 'w', encoding='utf-8') as f:
      yaml.dump(
        self.model_dump(exclude_none=True, exclude={'prefix'}),
        f,
        encoding='utf-8',
        sort_keys=False,
      )
    return f'Workflow is saved to {str(path)}'

  def compile(self) -> None:
    for step in self.steps:
      new_queries = []
      for query in step.queries:
        if isinstance(query, QueryFolder):
          for q in query.queries:
            new_queries.append(q.to_query(self.prefix))
        else:
          new_queries.append(query.to_query(self.prefix))
      step.queries = new_queries


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
