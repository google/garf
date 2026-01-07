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
from __future__ import annotations

import os
import pathlib

import pydantic
import smart_open
import yaml

from garf_executors.execution_context import ExecutionContext


class QueryPath(pydantic.BaseModel):
  """Path file with query."""

  path: str


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
  """

  fetcher: str | None = None
  alias: str | None = None
  queries: list[QueryPath | QueryDefinition] | None = None

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
  """

  steps: list[ExecutionStep]

  @classmethod
  def from_file(cls, path: str | pathlib.Path | os.PathLike[str]) -> Workflow:
    """Builds workflow from local or remote yaml file."""
    with smart_open.open(path, 'r', encoding='utf-8') as f:
      data = yaml.safe_load(f)
    return Workflow(steps=data.get('steps'))

  def save(self, path: str | pathlib.Path | os.PathLike[str]) -> str:
    """Saves workflow to local or remote yaml file."""
    with smart_open.open(path, 'w', encoding='utf-8') as f:
      yaml.dump(
        self.model_dump(exclude_none=True).get('steps'), f, encoding='utf-8'
      )
    return f'Workflow is saved to {str(path)}'
