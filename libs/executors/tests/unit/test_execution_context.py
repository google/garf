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

import yaml
import pytest
from garf_core import query_editor
from garf_executors.execution_context import ExecutionContext


class TestExecutionContext:
  def test_default_execution_context_creates_correct_query_parameters(self):
    context = ExecutionContext()
    assert context.query_parameters == query_editor.GarfQueryParameters(
      macro={}, template={}
    )

  def test_from_file_returns_correct_context_from_empty_data(self, tmp_path):
    tmp_config = tmp_path / 'config.yaml'
    data = {}
    with open(tmp_config, 'w', encoding='utf-8') as f:
      yaml.dump(data, f, encoding='utf-8')
    config = ExecutionContext.from_file(tmp_config)
    assert config == ExecutionContext()

  def test_from_file_returns_correct_context_from_data(self, tmp_path):
    tmp_config = tmp_path / 'config.yaml'
    data = {
      'query_parameters': {
        'macro': {
          'start_date': '2025-01-01',
        },
        'template': {
          'cohorts': 1,
        },
      },
      'fetcher_parameters': {
        'id': [1, 2, 3],
      },
      'writer': 'csv',
      'writer_parameters': {
        'destination_folder': '/tmp',
      },
    }
    with open(tmp_config, 'w', encoding='utf-8') as f:
      yaml.dump(data, f, encoding='utf-8')
    context = ExecutionContext.from_file(tmp_config)
    expected_context = ExecutionContext(**data)
    assert context == expected_context

  def test_save_returns_correct_data(self, tmp_path):
    tmp_config = tmp_path / 'config.yaml'
    data = {
      'query_parameters': {
        'macro': {
          'start_date': '2025-01-01',
        },
        'template': {
          'cohorts': 1,
        },
      },
      'fetcher_parameters': {
        'id': [1, 2, 3],
      },
      'writer': 'csv',
      'writer_parameters': {
        'destination_folder': '/tmp',
      },
    }
    context = ExecutionContext(**data)
    context.save(tmp_config)
    with open(tmp_config, 'r', encoding='utf-8') as f:
      config_data = yaml.safe_load(f)
    # Due to backward compatibility conversion, writers and writers_parameters
    # will be added automatically, so we check that original fields are preserved
    assert config_data['writer'] == data['writer']
    assert config_data['writer_parameters'] == data['writer_parameters']
    assert config_data['writers'] == [data['writer']]
    assert config_data['writers_parameters'] == [data['writer_parameters']]

  def test_multiple_writers_creates_multiple_clients(self, tmp_path):
    context = ExecutionContext(
      writers=['console', 'json'],
      writers_parameters=[
        {'page_size': '10'},
        {'destination_folder': str(tmp_path)},
      ],
    )
    writer_clients = context.writer_clients
    assert len(writer_clients) == 2
    assert writer_clients[0].__class__.__name__ == 'ConsoleWriter'
    assert writer_clients[1].__class__.__name__ == 'JsonWriter'

  def test_multiple_writers_without_parameters_creates_empty_dicts(self):
    context = ExecutionContext(
      writers=['console', 'json'],
    )
    writer_clients = context.writer_clients
    assert len(writer_clients) == 2

  def test_backward_compatibility_single_writer_still_works(self, tmp_path):
    context = ExecutionContext(
      writer='json',
      writer_parameters={'destination_folder': str(tmp_path)},
    )
    # Should work with writer_client property
    writer_client = context.writer_client
    assert writer_client.__class__.__name__ == 'JsonWriter'
    # Should also work with writer_clients property
    writer_clients = context.writer_clients
    assert len(writer_clients) == 1
    assert writer_clients[0].__class__.__name__ == 'JsonWriter'

  def test_writers_parameters_length_mismatch_raises_error(self):
    with pytest.raises(ValueError, match='writers_parameters length'):
      ExecutionContext(
        writers=['console', 'json'],
        writers_parameters=[{'page_size': '10'}],  # Only one param dict for two writers
      )

  def test_from_file_with_multiple_writers(self, tmp_path):
    tmp_config = tmp_path / 'config.yaml'
    data = {
      'writers': ['console', 'json'],
      'writers_parameters': [
        {'page_size': '10'},
        {'destination_folder': '/tmp'},
      ],
    }
    with open(tmp_config, 'w', encoding='utf-8') as f:
      yaml.dump(data, f, encoding='utf-8')
    context = ExecutionContext.from_file(tmp_config)
    assert context.writers == ['console', 'json']
    assert len(context.writer_clients) == 2