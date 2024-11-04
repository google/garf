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

import datetime

import pytest
from gaarf_core import report


@pytest.fixture
def single_column_data():
  results = [[1], [2], [3]]
  columns = ['column_1']
  return report.GaarfReport(results, columns)


@pytest.fixture
def sample_data():
  results = [[1, 'two', [3, 4]]]
  columns = ['column_1', 'column_2', 'column_3']
  return report.GaarfReport(results, columns)


@pytest.fixture
def sample_data_with_dates():
  results = [
    [1, datetime.datetime.now(), datetime.datetime.now().date()],
  ]
  columns = ['column_1', 'datetime', 'date']
  return report.GaarfReport(results, columns)
