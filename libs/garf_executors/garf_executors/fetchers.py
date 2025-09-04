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

from garf_core import exceptions, report_fetcher


def find_fetchers() -> set[str]:
  """Identifiers all available report fetchers."""
  return {fetcher.name for fetcher in entry_points(group='garf')}


def get_report_fetcher(source: str) -> type[report_fetcher.ApiReportFetcher]:
  """Loads report fetcher for a given source.

  Args:
    source: Alias for a source associated with a fetcher.

  Returns:
    Class for a found report fetcher.

  Raises:
    ApiReportFetcherError: When fetcher cannot be loaded.
    MissingApiReportFetcherError: When fetcher not found.
  """
  if source not in find_fetchers():
    raise report_fetcher.MissingApiReportFetcherError(source)
  fetchers = entry_points(group='garf')
  for fetcher in fetchers:
    if fetcher.name == source:
      try:
        fetcher_module = fetcher.load()
        for name, obj in inspect.getmembers(fetcher_module):
          if inspect.isclass(obj) and issubclass(
            obj, report_fetcher.ApiReportFetcher
          ):
            return getattr(fetcher_module, name)
      except ModuleNotFoundError:
        continue
  raise exceptions.ApiReportFetcherError(
    f'No fetcher available for the source "{source}"'
  )
