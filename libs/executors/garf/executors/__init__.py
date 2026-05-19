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
"""Executors to fetch data from various APIs."""

from __future__ import annotations

from garf.executors import exceptions
from garf.executors.api_executor import ApiQueryExecutor

__all__ = [
  'ApiQueryExecutor',
]

__version__ = '1.4.3'


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
