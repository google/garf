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
import json

import pytest
from garf.community.experimental.media_tagging.query_editor import (
  MediaTaggingApiQuery,
)
from garf.core import query_editor


class TestMediaTaggingApiQuery:
  def test_generate_raises_error_on_unsupported_resource(self):
    with pytest.raises(query_editor.GarfResourceError):
      MediaTaggingApiQuery(
        text='SELECT media_url FROM unknown_resource'
      ).generate()

  def test_generate_processes_filters(self):
    query = """
        SELECT
          media_url
        FROM tag
        WHERE
          tagger_type = gemini
          AND media_type = IMAGE
          AND media_path IN ([\'example.com, example2.com])
          AND tagging_options.custom_prompt = "Do something"
          AND tagging_options.model_name = 'gemini-3.0-flash'
      """
    query_elements = MediaTaggingApiQuery(text=query).generate()
    expected_filters = {
      'tagger_type': 'gemini',
      'media_type': 'IMAGE',
      'media_path': ['example.com', 'example2.com'],
      'tagging_options': {
        'custom_prompt': 'Do something',
        'model_name': 'gemini-3.0-flash',
      },
    }
    assert query_elements.filters == expected_filters

  def test_generate_processes_schema_from_path(self, tmp_path):
    custom_schema = {'type': 'boolean'}
    tmp_schema_path = tmp_path / 'test-schema.json'
    with open(tmp_schema_path, 'w', encoding='utf-8') as f:
      json.dump(custom_schema, f)
    query = f"""
        SELECT
          media_url
        FROM tag
        WHERE
          tagger_type = gemini
          AND media_type = IMAGE
          AND media_path IN (example.com, 'example2.com')
          AND tagging_options.custom_schema = '{tmp_schema_path}'
      """
    query_elements = MediaTaggingApiQuery(text=query).generate()
    assert (
      query_elements.filters.get('tagging_options').get('custom_schema')
      == custom_schema
    )

  def test_generate_processes_schema_from_builtin(self):
    custom_schema = {'type': 'boolean'}
    builtin_schema = 'boolean'
    query = f"""
        SELECT
          media_url
        FROM tag
        WHERE
          tagger_type = gemini
          AND media_type = IMAGE
          AND media_path IN (example.com, example2.com)
          AND tagging_options.custom_prompt = "Do something"
          AND tagging_options.model_name = 'gemini-3.0-flash'
          AND tagging_options.custom_schema = '{builtin_schema}'
      """
    query_elements = MediaTaggingApiQuery(text=query).generate()
    assert (
      query_elements.filters.get('tagging_options').get('custom_schema')
      == custom_schema
    )

  def test_generate_processes_enum_schema_from_builtin(self):
    builtin_schema = 'enum:Category1,Category2'
    query = f"""
        SELECT
          media_url
        FROM tag
        WHERE
          tagger_type = gemini
          AND media_type = IMAGE
          AND media_path IN (example.com, example2.com)
          AND tagging_options.custom_prompt = "Do something"
          AND tagging_options.model_name = 'gemini-3.0-flash'
          AND tagging_options.custom_schema = '{builtin_schema}'
      """
    query_elements = MediaTaggingApiQuery(text=query).generate()
    expected_schema = {'type': 'string', 'enum': ['Category1', 'Category2']}
    assert (
      query_elements.filters.get('tagging_options').get('custom_schema')
      == expected_schema
    )

  @pytest.mark.skip('Inline schemas are not supported')
  def test_generate_processes_schema_from_inline_macro(self):
    custom_schema = {'type': 'boolean'}
    query = """
        SELECT
          media_url
        FROM tag
        WHERE
          tagger_type = gemini
          AND media_type = IMAGE
          AND media_path IN (example.com, example2.com)
          AND tagging_options.custom_prompt = "Do something"
          AND tagging_options.model_name = 'gemini-3.0-flash'
          AND tagging_options.custom_schema = '{inline_schema}'
      """
    query_elements = MediaTaggingApiQuery(
      text=query,
      args=query_editor.GarfQueryParameters(
        macro={'inline_schema': json.dumps(custom_schema)}
      ),
    ).generate()
    assert (
      query_elements.filters.get('tagging_options').get('custom_schema')
      == custom_schema
    )
