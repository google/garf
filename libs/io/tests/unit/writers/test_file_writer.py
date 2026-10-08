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
import pathlib

import pytest
from garf.io import exceptions
from garf.io.writers import file_writer


class TestFileWriter:
  def test_create_dir_from_local_path_creates_folder(self, tmp_path):
    destination_folder = tmp_path / 'destination_folder'
    writer = file_writer.FileWriter(destination_folder=destination_folder)
    writer.create_dir()
    assert destination_folder.is_dir()

  def test_create_dir_from_local_path_creates_folder_from_allowed_folders(
    self, tmp_path, monkeypatch
  ):
    monkeypatch.setenv('GARF_ALLOWED_FOLDERS', str(tmp_path))
    destination_folder = tmp_path / 'destination_folder'
    writer = file_writer.FileWriter(destination_folder=destination_folder)
    writer.create_dir()
    assert destination_folder.is_dir()

  def test_create_dir_from_remote_path_does_not_create_folder(
    self, monkeypatch
  ):
    destination_folder = 'gs://fake-bucket,s3://fake-bucket'
    monkeypatch.setenv('GARF_ALLOWED_FOLDERS', destination_folder)
    writer = file_writer.FileWriter(destination_folder=destination_folder)
    writer.create_dir()
    expected_path = pathlib.Path(destination_folder)
    assert not expected_path.is_dir()

  def test_create_dir_raises_error_on_not_allowed_folder(
    self, tmp_path, monkeypatch
  ):
    monkeypatch.setenv('GARF_ALLOWED_FOLDERS', '/home/user/garf')
    destination_folder = tmp_path / 'destination_folder'
    with pytest.raises(
      exceptions.GarfIoError,
      match=f'Destination folder {destination_folder} not supported',
    ):
      file_writer.FileWriter(destination_folder=destination_folder)
