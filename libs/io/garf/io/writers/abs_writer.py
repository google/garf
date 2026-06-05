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
"""Defines an interface for Abstract writer."""

from __future__ import annotations

import abc
import asyncio
import logging
from typing import Literal

import pydantic
from garf.core.report import GarfReport
from garf.io import formatter
from garf.io.telemetry import tracer

logger = logging.getLogger(__name__)


class WriterOptions(pydantic.BaseModel):
  model_config = pydantic.ConfigDict(extra='allow')

  array_handling: Literal['strings', 'arrays'] = 'strings'
  array_separator: str = '|'
  date_handling: Literal['strings', 'dates', 'datetimes', 'timestamps'] = (
    'strings'
  )
  date_format_string: str | None = None
  suffix: str | None = None
  prefix: str | None = None


class AbsWriter(abc.ABC):
  """Base class for defining writers."""

  def __init__(
    self,
    options: WriterOptions | None = None,
    **kwargs,
  ) -> None:
    """Initializes AbsWriter."""
    self.options = options if options else WriterOptions(**kwargs)
    self.kwargs = kwargs

  async def awrite(self, report: GarfReport, destination: str) -> str | None:
    """Writes report to destination."""
    return await asyncio.to_thread(
      self.write, report=report, destination=destination
    )

  @abc.abstractmethod
  def write(self, report: GarfReport, destination: str) -> str | None:
    """Writes report to destination."""

  @tracer.start_as_current_span('format_for_write')
  def format_for_write(self, report: GarfReport) -> GarfReport:
    """Prepares report for writing."""
    array_handling_strategy = formatter.ArrayHandlingStrategy(
      type_=self.options.array_handling, delimiter=self.options.array_separator
    )
    date_handling_strategy = formatter.DateHandlingStrategy(
      type=self.options.date_handling,
      format_string=self.options.date_format_string,
    )
    return formatter.format_report_for_writing(
      report, [array_handling_strategy, date_handling_strategy]
    )
