# Copyright 2022 Google LLC
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
from garf_io import writer


@pytest.mark.parametrize('option', ['bq', 'bigquery'])
def test_create_writer_returns_correct_fields_for_bq_option(option):
  bq_writer = writer.create_writer(
    option, project='fake_project', dataset='fake_dataset'
  )
  assert bq_writer.dataset_id == 'fake_project.fake_dataset'


def test_create_writer_returns_correct_fields_for_csv_option():
  csv_writer = writer.create_writer('csv', destination_folder='/fake_folder')
  assert csv_writer.destination_folder == '/fake_folder'


def test_create_writer_returns_correct_fields_for_sheets_option():
  sheet_writer = writer.create_writer(
    'sheet',
    share_with='1@google.com',
    credentials_file='home/me/client_secret.json',
  )
  assert sheet_writer.share_with == '1@google.com'
  assert sheet_writer.credentials_file == 'home/me/client_secret.json'


def test_create_writer_returns_correct_fields_for_sqldb_option():
  sqlalchemy_writer = writer.create_writer(
    'sqldb', connection_string='protocol://user:password@host:port/db'
  )
  assert sqlalchemy_writer.connection_string == (
    'protocol://user:password@host:port/db'
  )


def test_create_writer_returns_correct_fields_for_json_option():
  json_writer = writer.create_writer('json', destination_folder='/fake_folder')
  assert json_writer.destination_folder == '/fake_folder'


def test_null_writer_raises_unknown_writer_error():
  with pytest.raises(writer.GarfIoWriterError):
    writer.create_writer('non-existing-option')
