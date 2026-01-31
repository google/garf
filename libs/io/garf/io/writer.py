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
"""Module for defining writer factory."""

from __future__ import annotations

import enum
import inspect
import sys
from importlib.metadata import entry_points
from typing import Any

from garf.io import exceptions
from garf.io.telemetry import tracer
from garf.io.writers import abs_writer
from opentelemetry import trace


@tracer.start_as_current_span('get_writers')
def _get_writers():
  if sys.version_info.major == 3 and sys.version_info.minor == 9:
    try:
      writers = entry_points()['garf_writer']
    except KeyError:
      writers = []
  else:
    writers = entry_points(group='garf_writer')
  return writers


class StrEnumBase(str, enum.Enum):
  """String enum."""


_writer_options = {writer.name: writer.name for writer in _get_writers()}

WriterOption = enum.Enum(
  'WriterOption',
  _writer_options,
  type=StrEnumBase,
)


class GarfIoWriterError(exceptions.GarfIoError):
  """Writer specific exception."""


@tracer.start_as_current_span('create_writer')
def create_writer(
  writer_option: str | WriterOption, **kwargs: str
) -> type[abs_writer.AbsWriter]:
  """Factory function for creating concrete writer.

  Writer is created based on `writer_option` and possible `kwargs` needed
  to correctly instantiate it.

  Args:
    writer_option: Type of writer.
    kwargs: Any possible arguments needed to instantiate writer.

  Returns:
    Concrete instantiated writer.

  Raises:
    ImportError: When writer specific library is not installed.
    GarfIoError: When incorrect writer option is specified.
  """
  span = trace.get_current_span()
  try:
    WriterOption[writer_option]
  except KeyError as e:
    raise GarfIoWriterError(f'{writer_option} is unknown writer type!') from e
  found_writers = {}
  for writer in _get_writers():
    try:
      if writer.name != writer_option:
        continue
      writer_module = writer.load()
      for name, obj in inspect.getmembers(writer_module):
        if inspect.isclass(obj) and issubclass(obj, abs_writer.AbsWriter):
          found_writers[writer.name] = getattr(writer_module, name)
    except ModuleNotFoundError:
      continue
    except ImportError as e:
      if writer_option == writer.name:
        raise e
      continue
  if concrete_writer := found_writers.get(writer_option):
    span.set_attribute('writer.alias', writer_option)
    for k, v in kwargs.items():
      span.set_attribute(f'{writer_option}.{k}', v)
    return concrete_writer(**kwargs)
  raise GarfIoWriterError(f'Failed to load {writer_option}!')


def setup_writers(
  writers: list[str], writer_parameters: dict[str, Any] | None = None
) -> list[abs_writer.AbsWriter]:
  """Returns list of writer clients."""
  if isinstance(writers, str):
    writers = [writers]
  if writer_parameters is None:
    writer_parameters = {}

  clients = []
  for writer_type in writers:
    writer_client = create_writer(writer_type, **writer_parameters)
    if writer_type in ('bq', 'bigquery'):
      _ = writer_client.create_or_get_dataset()
    if writer_type in ('sheet', 'sheets'):
      writer_client.create_or_get_spreadsheet()
    clients.append(writer_client)
  return clients
