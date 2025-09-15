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

import abc

import smart_open
from typing_extensions import override


class AbsReader(abc.ABC):
  """Base class for reading queries."""

  @abc.abstractmethod
  def read(self, query_path: str, **kwargs: str):
    """Reads query from local or remote storage."""


class FileReader(AbsReader):
  """Reads from file."""

  @override
  def read(self, query_path, **kwargs):
    with smart_open.open(query_path, 'r') as f:
      return f.read()


class ConsoleReader(AbsReader):
  """Read query from standard input."""

  @override
  def read(self, query_path, **kwargs):
    return query_path


class NullReader(AbsReader):
  """Invalid reader."""

  def __init__(self, reader_option, **kwargs):
    raise ValueError(f'{reader_option} is unknown reader type!')

  def read(self):
    print('Unknown reader type!')


_READER_OPTIONS = {
  'file': FileReader,
  'console': ConsoleReader,
}


def create_reader(reader_option: str, **kwargs) -> AbsReader:
  if reader := _READER_OPTIONS.get(reader_option):
    return reader(**kwargs)
  return NullReader(reader_option)
