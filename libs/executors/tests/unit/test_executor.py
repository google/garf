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

import garf.core
import pytest
from garf.executors import executor
from garf.io import exceptions, writer


def test_write_many_success():
  test_report = garf.core.GarfReport(results=[[1]], column_names=['test'])
  assert test_report.results
  writer_clients = [writer.create_writer('console')]
  results = executor.write_many(
    writer_clients=writer_clients, results=test_report, title='test'
  )
  assert results == '[Console] - test'
  assert not test_report.results


def test_write_many_failure(mocker):
  test_report = garf.core.GarfReport(results=[[1]], column_names=['test'])
  writer_clients = [writer.create_writer('console')]
  test_exception = ValueError('test error')
  mocker.patch(
    'garf.io.writers.console_writer.ConsoleWriter.write',
    side_effect=test_exception,
  )
  assert test_report.results
  with pytest.raises(exceptions.GarfIoError, match=f'[{test_exception}]'):
    executor.write_many(
      writer_clients=writer_clients, results=test_report, title='test'
    )
  assert not test_report.results
