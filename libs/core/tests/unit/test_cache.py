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

import pytest
from garf.core import cache, query_editor, report


class TestGarfCache:
  @pytest.fixture()
  def test_load_returns_report_from_cache(self, tmp_path):
    test_cache = cache.GarfCache(location=str(tmp_path))
    test_report = report.GarfReport(results=[[1]], column_names=['test'])
    query = query_editor.QuerySpecification(
      text='SELECT test FROM test'
    ).generate()

    test_cache.save(test_report, query)
    loaded_report = cache.load(query)

    assert loaded_report == test_cache

  def test_load_raises_error_on_outdated_cache(self, tmp_path):
    test_cache = cache.GarfCache(location=str(tmp_path), ttl_seconds=0)
    test_report = report.GarfReport(results=[[1]], column_names=['test'])
    query = query_editor.QuerySpecification(
      text='SELECT test FROM test'
    ).generate()

    test_cache.save(test_report, query)
    with pytest.raises(cache.GarfCacheFileNotFoundError):
      test_cache.load(query)
