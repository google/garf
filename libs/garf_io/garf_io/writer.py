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

from importlib import import_module

from garf_io.writers import abs_writer


def create_writer(
  writer_option: str, **kwargs: str
) -> type[abs_writer.AbsWriter]:
  """Factory function for creating concrete writer.

  Writer is created based on `writer_option` and possible `kwargs` needed
  to correctly instantiate it.

  Args:
      writer_option: Type of writer.
      kwargs: Any possible arguments needed o instantiate writer.

  Returns:
      Concrete instantiated writer.
  """
  if writer_option in ('bq', 'bigquery'):
    writer_module = import_module('garf_io.writers.bigquery_writer')
    return writer_module.BigQueryWriter(**kwargs)
  if writer_option == 'sqldb':
    writer_module = import_module('garf_io.writers.sqldb_writer')
    return writer_module.SqlAlchemyWriter(**kwargs)
  if writer_option in ('sheet', 'sheets'):
    writer_module = import_module('garf_io.writers.sheets_writer')
    return writer_module.SheetWriter(**kwargs)
  if writer_option == 'console':
    writer_module = import_module('garf_io.writers.console_writer')
    return writer_module.ConsoleWriter(**kwargs)
  if writer_option == 'csv':
    writer_module = import_module('garf_io.writers.csv_writer')
    return writer_module.CsvWriter(**kwargs)
  if writer_option == 'json':
    writer_module = import_module('garf_io.writers.json_writer')
    return writer_module.JsonWriter(**kwargs)
  return import_module('garf_io.writers.null_writer').NullWriter(writer_option)
