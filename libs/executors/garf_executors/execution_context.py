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
    writer: Type of writer to use (deprecated, use writers instead).
    writer_parameters: Optional parameters to setup writer (deprecated, use writers_parameters instead).
    writers: List of writer types to use. If specified, multiple writers will be used.
    writers_parameters: List of parameter dicts for each writer. Must match length of writers.
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
  writers: list[str] | None = None
  writers_parameters: list[dict[str, str]] | None = None

  def model_post_init(self, __context__) -> None:
    if self.fetcher_parameters is None:
      self.fetcher_parameters = {}
    if self.writer_parameters is None:
      self.writer_parameters = {}
    if not self.query_parameters:
      self.query_parameters = query_editor.GarfQueryParameters()
    # Backward compatibility: if writer is set but writers is not, convert to writers list
    if self.writer and not self.writers:
      self.writers = [self.writer]
      if self.writer_parameters:
        self.writers_parameters = [self.writer_parameters]
      else:
        self.writers_parameters = [{}]
    # Validate writers_parameters length matches writers length
    if self.writers and self.writers_parameters:
      if len(self.writers) != len(self.writers_parameters):
        raise ValueError(
          f'writers_parameters length ({len(self.writers_parameters)}) '
          f'must match writers length ({len(self.writers)})'
        )
    elif self.writers and not self.writers_parameters:
      # If writers is set but writers_parameters is not, create empty dicts
      self.writers_parameters = [{}] * len(self.writers)

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
    """Returns single writer client (for backward compatibility)."""
    if self.writers and len(self.writers) > 0:
      # Use first writer for backward compatibility
      writer_type = self.writers[0]
      writer_params = (
        self.writers_parameters[0] if self.writers_parameters else {}
      )
    else:
      writer_type = self.writer
      writer_params = self.writer_parameters or {}
    
    if not writer_type:
      raise ValueError('No writer specified')
    
    writer_client = writer.create_writer(writer_type, **writer_params)
    if writer_type == 'bq':
      _ = writer_client.create_or_get_dataset()
    if writer_type == 'sheet':
      writer_client.init_client()
    return writer_client

  @property
  def writer_clients(self) -> list[abs_writer.AbsWriter]:
    """Returns list of writer clients for multiple writers."""
    # Handle backward compatibility: if only writer is set, convert to writers list
    writers_to_use = self.writers
    writers_params_to_use = self.writers_parameters
    
    if not writers_to_use and self.writer:
      writers_to_use = [self.writer]
      writers_params_to_use = [self.writer_parameters] if self.writer_parameters else [{}]
    
    if not writers_to_use:
      return []
    
    clients = []
    for i, writer_type in enumerate(writers_to_use):
      writer_params = (
        writers_params_to_use[i] if writers_params_to_use else {}
      )
      writer_client = writer.create_writer(writer_type, **writer_params)
      if writer_type == 'bq':
        _ = writer_client.create_or_get_dataset()
      if writer_type == 'sheet':
        writer_client.init_client()
      clients.append(writer_client)
    return clients
