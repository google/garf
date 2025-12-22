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
import logging
import sys
from importlib.metadata import entry_points

from garf_core import report_fetcher

from garf_executors.telemetry import tracer

logger = logging.getLogger(name='garf_executors.fetchers')


@tracer.start_as_current_span('find_fetchers')
def find_fetchers() -> set[str]:
  """Identifiers all available report fetchers."""
  if entrypoints := _get_entrypoints('garf'):
    return {fetcher.name for fetcher in entrypoints}
  return set()


@tracer.start_as_current_span('get_report_fetcher')
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
  for fetcher in _get_entrypoints('garf'):
    if fetcher.name == source:
      try:
        with tracer.start_as_current_span('load_fetcher_module') as span:
          fetcher_module = fetcher.load()
          span.set_attribute('loaded_module', fetcher_module.__name__)
        for name, obj in inspect.getmembers(fetcher_module):
          if inspect.isclass(obj) and issubclass(
            obj, report_fetcher.ApiReportFetcher
          ):
            return getattr(fetcher_module, name)
      except ModuleNotFoundError as e:
        raise report_fetcher.ApiReportFetcherError(
          f'Failed to load fetcher for source {source}, reason: {e}'
        )
  raise report_fetcher.ApiReportFetcherError(
    f'No fetcher available for the source "{source}"'
  )


def _get_entrypoints(group='garf'):
  if sys.version_info.major == 3 and sys.version_info.minor == 9:
    try:
      fetchers = entry_points()[group]
    except KeyError:
      fetchers = []
  else:
    fetchers = entry_points(group=group)
  return fetchers
