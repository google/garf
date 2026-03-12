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

"""Stores mapping between API aliases and their execution context."""

from __future__ import annotations

import os
import pathlib

import pydantic
import smart_open
import yaml
from garf.core import query_editor
from garf.executors import utils
from garf.executors.execution_context import ExecutionContext
from typing_extensions import Self


class Config(pydantic.BaseModel):
  """Stores necessary parameters for one or multiple API sources.

  Attributes:
    source: Mapping between API source alias and execution parameters.
  """

  sources: dict[str, ExecutionContext]
  global_parameters: ExecutionContext | None = None

  @classmethod
  def from_file(cls, path: str | pathlib.Path | os.PathLike[str]) -> Config:
    """Builds config from local or remote yaml file."""
    with smart_open.open(path, 'r', encoding='utf-8') as f:
      data = yaml.safe_load(f)
    return Config(**data)

  def save(self, path: str | pathlib.Path | os.PathLike[str]) -> str:
    """Saves config to local or remote yaml file."""
    with smart_open.open(path, 'w', encoding='utf-8') as f:
      yaml.dump(self.model_dump(exclude_none=True), f, encoding='utf-8')
    return f'Config is saved to {str(path)}'

  def expand(self) -> Self:
    if global_parameters := self.global_parameters:
      if query_parameters := global_parameters.query_parameters:
        common_parameters = {
          k: v for k, v in query_parameters.model_dump().items() if v
        }
        for k, s in self.sources.items():
          source_parameters = {
            k: v for k, v in s.query_parameters.model_dump().items() if v
          }
          source_joined_parameters = utils.merge_dicts(
            dict(common_parameters), source_parameters
          )
          s.query_parameters = query_editor.GarfQueryParameters(
            **source_joined_parameters
          )
      if writer_parameters := global_parameters.writer_parameters:
        common_parameters = {k: v for k, v in writer_parameters.items() if v}
        for k, s in self.sources.items():
          writer_parameters = {
            k: v for k, v in s.writer_parameters.items() if v
          }
          writer_joined_parameters = utils.merge_dicts(
            dict(common_parameters), writer_parameters
          )
          s.writer_parameters = writer_joined_parameters
      if fetcher_parameters := global_parameters.fetcher_parameters:
        common_parameters = {k: v for k, v in fetcher_parameters.items() if v}
        for k, s in self.sources.items():
          fetcher_parameters = {
            k: v for k, v in s.fetcher_parameters.items() if v
          }
          fetcher_joined_parameters = utils.merge_dicts(
            dict(common_parameters), fetcher_parameters
          )
          s.fetcher_parameters = fetcher_joined_parameters

    return self
