# Copyright 2024 Google LLC
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

import pytest

from garf_io import reader


def test_console_reader():
  console_reader = reader.ConsoleReader()
  expected = 'SELECT 1'
  assert expected == console_reader.read(expected)


@pytest.fixture
def reader_factory():
  return reader.ReaderFactory()


def test_reader_factory_load(reader_factory):
  assert reader_factory.reader_options == {
    'file': reader.FileReader,
    'console': reader.ConsoleReader,
  }


def test_reader_factory_inits(reader_factory):
  file_reader = reader_factory.create_reader('file')
  console_reader = reader_factory.create_reader('console')
  assert isinstance(file_reader, reader.FileReader)
  assert isinstance(console_reader, reader.ConsoleReader)


def test_null_reader_raises_unknown_reader_error(reader_factory):
  with pytest.raises(ValueError):
    reader_factory.create_reader('non-existing-option')
