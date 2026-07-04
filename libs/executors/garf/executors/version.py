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
from __future__ import annotations

from garf.core import version as core_version
from garf.executors import exceptions
from garf.io import version as io_version

__version__ = '1.6.1'


def validate_version(version: str | None = None):
  if not version:
    return True
  library_version = tuple(map(int, __version__.split('.')))
  checked_version = tuple(map(int, version.split('.')))
  if library_version < checked_version:
    raise exceptions.GarfExecutorError(
      f'Garf version ({__version__}) is below required by workflow - {version}.'
    )
  return True


core_version = core_version.__version__
io_version = io_version.__version__
