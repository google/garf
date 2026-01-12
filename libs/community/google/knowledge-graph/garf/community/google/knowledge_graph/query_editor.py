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
"""Defines KnowledgeGraphApiQuery."""

from garf.core import query_editor
from typing_extensions import Self


class KnowledgeGraphApiQuery(query_editor.QuerySpecification):
  """Query to Knowledge Graph Search api."""

  def __init__(
    self,
    text: str,
    title: str | None = None,
    args: dict[str, str] | None = None,
    **kwargs,
  ) -> None:
    """Initializes KnowledgeGraphApiQuery."""
    super().__init__(text, title, args, **kwargs)

  def extract_column_names(self) -> Self:
    """Removes extra symbols from column names."""
    for line in self._extract_query_lines():
      line_elements = query_editor.ExtractedLineElements.from_query_line(line)
      self.query.column_names.append(line_elements.alias.replace('@', ''))
    return self
