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

"""Simulates response from API based on a query."""

from __future__ import annotations

import logging
from typing import Any

import pydantic

from garf_core import api_clients, exceptions, parsers, query_editor, report

logger = logging.getLogger(__name__)


class GarfApiReportSimulatorError(exceptions.GarfError):
  """Simulator specific exception."""


class SimulatorSpecification(pydantic.BaseModel):
  model_config = pydantic.ConfigDict(extra='allow')

  n_rows: int = 10


class ApiReportSimulator:
  def __init__(
    self,
    api_client: api_clients.BaseClient,
    parser: type[parsers.BaseParser] = parsers.DictParser,
    query_specification_builder: type[query_editor.QuerySpecification] = (
      query_editor.QuerySpecification
    ),
    simulator_specification_builder: type[SimulatorSpecification] = (
      SimulatorSpecification
    ),
  ) -> None:
    self.api_client = api_client
    self.parser = parser
    self.query_specification_builder = query_specification_builder
    self.simulator_specification_builder = simulator_specification_builder

  def simulate(
    self,
    query_specification: str | query_editor.QuerySpecification,
    simulator_specification: SimulatorSpecification | None = None,
    **kwargs: str,
  ) -> report.GarfReport:
    if not isinstance(query_specification, query_editor.QuerySpecification):
      query_specification = self.query_specification_builder(
        text=str(query_specification),
      )
    query = query_specification.generate()
    try:
      response_types = self.api_client.get_types(query, **kwargs)
    except NotImplementedError as e:
      raise GarfApiReportSimulatorError(
        'Simulation is not supported for ApiClient '
        f'{self.api_client.__class__.__name__}'
      ) from e
    simulated_results = []
    if not simulator_specification:
      simulator_specification = self.simulator_specification_builder(**kwargs)
    for _ in range(simulator_specification.n_rows):
      simulated_results.append(self._generate_random_values(response_types))
    parsed_response = self.parser(query).parse_response(
      api_clients.GarfApiResponse(results=simulated_results)
    )

    return report.GarfReport(
      results=parsed_response,
      query_specification=query,
      column_names=[c for c in query.column_names if c != '_'],
    )

  def _generate_random_values(
    self,
    response_types: dict[str, Any],
  ) -> dict[str, Any]:
    results = {}
    type_mapping = {
      str: '',
      int: 1,
      float: 1,
      bool: True,
    }
    for key, value in response_types.items():
      if isinstance(value, dict):
        results[key] = self._generate_random_values(value)
      else:
        results[key] = type_mapping.get(value)
    return results
