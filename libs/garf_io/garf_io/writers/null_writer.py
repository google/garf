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
"""Base case of non-existing writer."""

from __future__ import annotations

from garf_core import report as garf_report
from garf_io.writers.abs_writer import AbsWriter


class NullWriter(AbsWriter):
  def __init__(self, writer_option, **kwargs):
    raise ValueError(f'{writer_option} is unknown writer type!')

  def write(self, report: garf_report.GarfReport, destination: str) -> None:
    print('Unknown writer type!')
