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

import pytest
from garf.core.query_parser import (
  Customizer,
  ExtractedLineElements,
  GarfVirtualColumnError,
  SliceField,
  VirtualColumn,
)


class TestExtractedLineElemens:
  @pytest.mark.parametrize(
    ('line', 'expected'),
    [
      (
        'field AS column',
        ExtractedLineElements(field='field', alias='column'),
      ),
      (
        'field',
        ExtractedLineElements(field='field', alias='field'),
      ),
      (
        '1 + 1 AS column',
        ExtractedLineElements(
          field=None,
          alias='column',
          virtual_column=VirtualColumn(
            type='expression',
            value='1 + 1',
            fields=[],
            substitute_expression='1 + 1',
          ),
        ),
      ),
      (
        'field + 1 AS column',
        ExtractedLineElements(
          field=None,
          alias='column',
          virtual_column=VirtualColumn(
            type='expression',
            value='field + 1',
            fields=['field'],
            substitute_expression='{field} + 1',
          ),
        ),
      ),
      (
        'field[0].value AS column',
        ExtractedLineElements(
          field='field',
          alias='column',
          customizer=Customizer(
            type='slice',
            value=SliceField(slice_literal=slice(0, 1, None), value='value'),
          ),
        ),
      ),
    ],
  )
  def test_from_query_line_returns_correct_elements(self, line, expected):
    elements = ExtractedLineElements.from_query_line(line)
    assert elements == expected

  def test_from_query_line_raises_error_on_unaliased_virtual_column(self):
    with pytest.raises(
      GarfVirtualColumnError,
      match='Virtual attributes should be aliased: 1',
    ):
      ExtractedLineElements.from_query_line('1')
