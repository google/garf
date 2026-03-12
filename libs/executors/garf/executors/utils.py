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

"""Common utilities for garf executors."""

import copy
from typing import Any


def merge_dicts(dict1: dict[str, Any], dict2: dict[str, Any]) -> dict[str, Any]:
  """Performs deep merging of nested dicts."""
  result = copy.deepcopy(dict1)
  for key, value in dict2.items():
    if (
      key in result
      and isinstance(result[key], dict)
      and isinstance(value, dict)
    ):
      result[key] = merge_dicts(result[key], value)
    else:
      result[key] = value
  return result
