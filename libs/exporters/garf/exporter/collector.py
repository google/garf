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

"""Collectors serves as a wrapper on top garf query."""

import os
import pathlib
from typing import Union

import pydantic
import smart_open
import yaml


class Collector(pydantic.BaseModel):
  """Stores API query with meta information.

  Attributes:
    query: Text of a query for an API.
    title: Identifier of a query.
    suffix: Optional element to be added to Prometheus metric.
  """

  query: str
  title: str
  suffix: str = ''


def load_collector_data(
  path_to_definitions: Union[str, os.PathLike[str], pathlib.Path],
) -> list[Collector]:
  """Loads collectors data from file or folder.

  Args:
    path_to_definitions: Local path to file / folder with collector definitions.

  Returns:
    Loaded collector definitions.
  """
  if isinstance(path_to_definitions, str):
    path_to_definitions = pathlib.Path(path_to_definitions)
  results = []
  if path_to_definitions.is_file():
    with smart_open.open(path_to_definitions, 'r', encoding='utf-8') as f:
      data = yaml.safe_load(f)
      for entry in data:
        results.append(Collector(**entry))
  else:
    for file in path_to_definitions.iterdir():
      if file.suffix == '.yaml':
        with smart_open.open(file, 'r', encoding='utf-8') as f:
          data = yaml.safe_load(f)
          for entry in data:
            results.append(Collector(**entry))
  return results
