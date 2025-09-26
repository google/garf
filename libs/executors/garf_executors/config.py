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

from garf_executors.execution_context import ExecutionContext


class Config(pydantic.BaseModel):
  """Stores necessary parameters for one or multiple API sources.

  Attributes:
    source: Mapping between API source alias and execution parameters.
  """

  sources: dict[str, ExecutionContext]

  @classmethod
  def from_file(cls, path: str | pathlib.Path | os.PathLike[str]) -> Config:
    """Builds config from local or remote yaml file."""
    with smart_open.open(path, 'r', encoding='utf-8') as f:
      data = yaml.safe_load(f)
    return Config(sources=data)

  def save(self, path: str | pathlib.Path | os.PathLike[str]) -> str:
    """Saves config to local or remote yaml file."""
    with smart_open.open(path, 'w', encoding='utf-8') as f:
      yaml.dump(self.model_dump().get('sources'), f, encoding='utf-8')
    return f'Config is saved to {str(path)}'
