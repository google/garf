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

  @pytest.mark.parametrize(
    ('column', 'time_partitioning_type', 'expected'),
    [
      (None, None, None),
      ('column', None, 'DAY'),
      ('column', 'DAY', 'DAY'),
    ],
  )
  def test_init_creates_correct_time_partitioning(
    self, column, time_partitioning_type, expected
  ):
    writer = bigquery_writer.BigQueryWriter(
      project='test',
      time_partitioning_column=column,
      time_partitioning_type=time_partitioning_type,
    )
    assert writer.time_partitioning_type == expected

  def test_init_raises_error_incorrect_time_partitioning(self):
    with pytest.raises(
      bigquery_writer.BigQueryWriterError,
      match='Unsupported time_partitioning type, choose one of: DAY, HOUR, MONTH, YEAR',
    ):
      bigquery_writer.BigQueryWriter(
        project='test',
        time_partitioning_column='column',
        time_partitioning_type='UNKNOWN_TYPE',
      )

  def test_init_creates_correct_range_partitioning_range(self):
    writer = bigquery_writer.BigQueryWriter(
      project='test',
      range_partitioning_column='column',
      range_partitioning_range='1:100:10',
    )
    assert writer.range_partitioning_range == {
      'start': 1,
      'end': 100,
      'interval': 10,
    }

  @pytest.mark.parametrize('partition_range', ['1', '1:2', '1:s:3', '1:2:3:4'])
  def test_init_raises_error_incorrect_range_partitioning(
    self, partition_range
  ):
    with pytest.raises(
      bigquery_writer.BigQueryWriterError,
      match='Unsupported range_partitioning_range',
    ):
      bigquery_writer.BigQueryWriter(
        project='test',
        range_partitioning_column='column',
        range_partitioning_range=partition_range,
      )
