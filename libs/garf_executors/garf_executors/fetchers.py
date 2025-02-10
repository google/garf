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

import inspect
from importlib.metadata import entry_points

from garf_core import report_fetcher


def get_report_fetchers() -> dict[str, report_fetcher.ApiReportFetcher]:
  fetchers = entry_points(group='garf')
  found_fetchers = {}
  for fetcher in fetchers:
    try:
      fetcher_module = fetcher.load()
      for name, obj in inspect.getmembers(fetcher_module):
        if inspect.isclass(obj) and issubclass(
          obj, report_fetcher.ApiReportFetcher
        ):
          found_fetchers[fetcher.name] = getattr(fetcher_module, name)
    except ModuleNotFoundError:
      continue
  return found_fetchers


FETCHERS = get_report_fetchers()
