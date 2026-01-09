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

import os

import garf.core
import pytest
from garf.io.writers import bigquery_writer
from google.cloud import bigquery


class TestBigQueryWriter:
  @pytest.mark.skipif(
    not os.environ.get('GOOGLE_CLOUD_PROJECT'),
    reason='GOOGLE_CLOUD_PROJECT env variable not set.',
  )
  def test_write(self):
    writer = bigquery_writer.BigQueryWriter(array_handling='arrays')
    report = garf.core.GarfReport(
      results=[
        [{'key': ['one', 'two']}, 'three'],
      ],
      column_names=['column1', 'column2'],
    )
    result = writer.write(report, 'test')
    assert result

  @pytest.mark.parametrize(
    ('disposition', 'expected'),
    [
      ('append', 'append'),
      ('replace', 'replace'),
      ('fail', 'fail'),
      ('write_append', 'append'),
      ('write_truncate', 'replace'),
      ('write_truncate_data', 'replace'),
      ('write_empty', 'fail'),
      (bigquery.WriteDisposition.WRITE_APPEND, 'append'),
      (bigquery.WriteDisposition.WRITE_TRUNCATE, 'replace'),
      (bigquery.WriteDisposition.WRITE_TRUNCATE_DATA, 'replace'),
      (bigquery.WriteDisposition.WRITE_EMPTY, 'fail'),
    ],
  )
  def test_init_creates_correct_write_disposition(self, disposition, expected):
    writer = bigquery_writer.BigQueryWriter(
      project='test', write_disposition=disposition
    )
    assert writer.write_disposition == expected
