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

"""Captures parameters for fetching data from APIs."""

from __future__ import annotations

import os
import pathlib

import pydantic
import smart_open
import yaml
from garf_core import query_editor
from garf_io import writer
from garf_io.writers import abs_writer


class ExecutionContext(pydantic.BaseModel):
  """Common context for executing one or more queries.

  Attributes:
    query_parameters: Parameters to dynamically change query text.
    fetcher_parameters: Parameters to specify fetching setup.
    writer: Type of writer to use.
    writer_parameters: Optional parameters to setup writer.
  """

  query_parameters: query_editor.GarfQueryParameters | None = pydantic.Field(
    default_factory=dict
  )
  fetcher_parameters: dict[str, str | bool | int | list[str | int]] | None = (
    pydantic.Field(default_factory=dict)
  )
  writer: str | None = None
  writer_parameters: dict[str, str] | None = pydantic.Field(
    default_factory=dict
  )

  def model_post_init(self, __context__) -> None:
    if self.fetcher_parameters is None:
      self.fetcher_parameters = {}
    if self.writer_parameters is None:
      self.writer_parameters = {}
    if not self.query_parameters:
      self.query_parameters = query_editor.GarfQueryParameters()

  @classmethod
  def from_file(
    cls, path: str | pathlib.Path | os.PathLike[str]
  ) -> ExecutionContext:
    """Builds context from local or remote yaml file."""
    with smart_open.open(path, 'r', encoding='utf-8') as f:
      data = yaml.safe_load(f)
    return ExecutionContext(**data)

  def save(self, path: str | pathlib.Path | os.PathLike[str]) -> str:
    """Saves context to local or remote yaml file."""
    with smart_open.open(path, 'w', encoding='utf-8') as f:
      yaml.dump(self.model_dump(), f, encoding='utf-8')
    return f'ExecutionContext is saved to {str(path)}'

  @property
  def writer_client(self) -> abs_writer.AbsWriter:
    writer_client = writer.create_writer(self.writer, **self.writer_parameters)
    if self.writer == 'bq':
      _ = writer_client.create_or_get_dataset()
    if self.writer == 'sheet':
      writer_client.init_client()
    return writer_client
