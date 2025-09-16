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

import os

import pytest
from garf_io.writers import sheets_writer


class TestSheetWriter:
  @pytest.mark.skipif(
    os.getenv('GARF_TEST_FULL') is None,
    reason='Modifies data in remote systems',
  )
  def test_write_returns_saved_location(self, single_column_data):
    writer = sheets_writer.SheetWriter()
    result = writer.write(single_column_data)

    assert 'Report is saved' in result
