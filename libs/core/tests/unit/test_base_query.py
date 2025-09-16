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

import dataclasses
from typing import ClassVar

import pydantic
from garf_core import base_query


class TestBaseQuery:
  def test_native_initialization(self):
    class TestQuery(base_query.BaseQuery):
      query_text = 'SELECT metric FROM resource WHERE status = {status}'

      def __init__(self, status: str = 'ENABLED'):
        self.status = status

    test_query = TestQuery()

    assert (
      str(test_query) == 'SELECT metric FROM resource WHERE status = ENABLED'
    )

  def test_dataclass_initialization(self):
    @dataclasses.dataclass
    class TestQuery(base_query.BaseQuery):
      query_text = 'SELECT metric FROM resource WHERE status = {status}'
      status: str = 'ENABLED'

    test_query = TestQuery()

    assert (
      str(test_query) == 'SELECT metric FROM resource WHERE status = ENABLED'
    )

  def test_old_initialization(self):
    class TestQuery(base_query.BaseQuery):
      def __init__(self, status: str = 'ENABLED'):
        self.query_text = 'SELECT metric FROM resource WHERE status = {status}'
        self.status = status

    test_query = TestQuery()

    assert (
      str(test_query) == 'SELECT metric FROM resource WHERE status = ENABLED'
    )

  def test_pydantic_initialization(self):
    class TestQuery(base_query.BaseQuery, pydantic.BaseModel):
      query_text: ClassVar[str] = (
        'SELECT metric FROM resource WHERE status = {status}'
      )
      status: str = 'ENABLED'

    test_query = TestQuery()

    assert (
      str(test_query) == 'SELECT metric FROM resource WHERE status = ENABLED'
    )
