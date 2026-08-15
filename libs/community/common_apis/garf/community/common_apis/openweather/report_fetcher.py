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

"""Report fetcher for OpenWeatherMap API."""

from __future__ import annotations

import garf.core
from garf.community.common_apis.openweather import api_clients
from garf.core import parsers, report_fetcher


class OpenWeatherApiReportFetcher(garf.core.ApiReportFetcher):
  """garf source for the OpenWeatherMap API (``--source openweather``).

  This source is a focused wrapper around the garf REST client that removes
  the boilerplate required when using ``--source rest`` against OpenWeatherMap:

  - The base endpoint URL is built in.
  - The API key is handled internally and never needs to appear in queries.
  - OpenWeather's single-object JSON responses are automatically normalised
    into the list-of-dicts format that all garf parsers expect.

  Compared to ``--source rest`` the queries are simpler::

      -- With --source rest you must know the endpoint and inject the key:
      SELECT main.temp FROM weather
      WHERE lat={lat} AND lon={lon} AND appid={api_key}

      -- With --source openweather the key is handled for you:
      SELECT main.temp FROM weather
      WHERE lat={lat} AND lon={lon}

  CLI usage::

      garf weather.sql --source openweather \\
        --source.api_key=YOUR_KEY \\
        --macro.lat=33.44 \\
        --macro.lon=-94.04 \\
        --output csv

  Python usage::

      from garf.community.common_apis.openweather import OpenWeatherApiReportFetcher

      fetcher = OpenWeatherApiReportFetcher(api_key='YOUR_KEY')
      report  = fetcher.fetch('SELECT main.temp FROM weather WHERE lat=33.44 AND lon=-94.04')

  Args:
    api_client: Pre-built :class:`~garf.community.common_apis.openweather.\
api_clients.OpenWeatherApiClient` instance.  When omitted a client is
      created automatically from ``api_key`` and ``endpoint`` kwargs.
    parser: Parser class used to convert API rows.  Defaults to
      :class:`~garf.core.parsers.NumericConverterDictParser` so numeric
      fields (temperature, humidity, wind speed, …) are returned as Python
      numbers rather than strings.
    api_key: OpenWeatherMap API key (required when ``api_client`` is not
      provided).
    endpoint: Override the default API base URL.
    **kwargs: Additional keyword arguments forwarded to the underlying client.

  Raises:
    ApiReportFetcherError: When neither ``api_client`` nor ``api_key`` is
      provided.
  """

  alias = 'openweather'

  def __init__(
    self,
    api_client: api_clients.OpenWeatherApiClient | None = None,
    parser: type[parsers.BaseParser] = parsers.NumericConverterDictParser,
    **kwargs: str,
  ) -> None:
    if not api_client:
      if not kwargs.get('api_key'):
        raise report_fetcher.ApiReportFetcherError(
          'OpenWeatherApiReportFetcher requires an api_key. '
          'Pass --source.api_key=YOUR_KEY on the CLI or provide the '
          'api_key keyword argument.'
        )
      api_client = api_clients.OpenWeatherApiClient(**kwargs)
    super().__init__(
      api_client=api_client,
      parser=parser,
      **kwargs,
    )
