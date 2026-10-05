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
import pytest
from garf.executors import utils


@pytest.mark.parametrize(
  'statement', ['-- Comment\nDROP TABLE test', 'SELECT 1; DROP table test']
)
def test_validate_query_raises_error_on_unsupported_statements(statement):
  assert not utils.is_valid_query(statement)


@pytest.mark.parametrize(
  'statement',
  ['-- Comment\nSELECT 1', 'SELECT 1; SELECT 2', 'WITH Temp AS (SELECT 1)'],
)
def test_validate_query_success(statement):
  assert utils.is_valid_query(statement)
