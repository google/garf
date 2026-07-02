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

import garf.core
from garf.community.prometheus import api_clients, query_editor, version


class PrometheusApiReportFetcher(garf.core.ApiReportFetcher):
  """Defines report fetcher for Prometheus API."""

  alias = 'prometheus'
  version = version.__version__

  def __init__(
    self,
    api_client: api_clients.PrometheusApiClient | None = None,
    parser: garf.core.parsers.DictParser = (
      garf.core.parsers.NumericConverterDictParser
    ),
    query_spec: query_editor.PrometheusApiQuery = (
      query_editor.PrometheusApiQuery
    ),
    parallel_threshold: int = 10,
    **kwargs: str,
  ) -> None:
    """Initializes PrometheusApiReportFetcher."""
    if not api_client:
      api_client = api_clients.PrometheusApiClient(**kwargs)
    self.parallel_threshold = parallel_threshold
    super().__init__(
      api_client=api_client,
      parser=parser,
      query_specification_builder=query_spec,
      **kwargs,
    )
