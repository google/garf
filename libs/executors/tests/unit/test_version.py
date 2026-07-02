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
import re

import pytest
from garf.executors import exceptions, version


def test_validate_version_raises_error_on_lower_version():
  test_version = '100000.10.4'
  with pytest.raises(
    exceptions.GarfExecutorError,
    match=re.escape(
      f'Garf version ({version.__version__}) is below required '
      f'by workflow - {test_version}.'
    ),
  ):
    version.validate_version(test_version)


@pytest.mark.parametrize(
  'test_version',
  [
    None,
    '0.0.0',
    '0.100000.100000',
    '1.0.0',
    version.__version__,
  ],
)
def test_validate_version_returns_true(test_version):
  assert version.validate_version(test_version)
