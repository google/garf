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

# pylint: disable=C0330, g-bad-import-order, g-multiple-import, missing-class-docstring, missing-module-docstring, missing-function-docstring

import json
import pathlib
import subprocess
import sys

import pytest
import yaml

_SCRIPT_PATH = pathlib.Path(__file__).parent


def _skip_python_39(command):
  if sys.version_info[1] < 10 and command.startswith('grf'):
    pytest.skip('Python 3.9 is not supported')


class TestCli:
  query = (
    'SELECT resource, dimensions.name AS name, metrics.clicks AS clicks '
    'FROM resource'
  )
  expected_output = [
    {
      'resource': 'Campaign A',
      'name': 'Ad Group 1',
      'clicks': 1500,
    },
    {
      'resource': 'Campaign B',
      'name': 'Ad Group 2',
      'clicks': 2300,
    },
    {
      'resource': 'Campaign C',
      'name': 'Ad Group 3',
      'clicks': 800,
    },
    {
      'resource': 'Campaign A',
      'name': 'Ad Group 4',
      'clicks': 3200,
    },
  ]

  @pytest.mark.parametrize('command', ['garf', 'grf execute'])
  def test_fake_source_from_console(self, command):
    _skip_python_39(command)
    fake_data = _SCRIPT_PATH / 'test.json'
    command = (
      f'{command} "{self.query}" --input console --source fake '
      f'--source.data_location={fake_data} '
      '--output console --console.format=json '
      '--loglevel ERROR'
    )
    result = subprocess.run(
      command,
      shell=True,
      check=False,
      capture_output=True,
      text=True,
    )

    assert result.returncode == 0
    assert json.loads(result.stdout) == self.expected_output

  @pytest.mark.parametrize('command', ['garf', 'grf execute'])
  def test_fake_source_from_file(self, tmp_path, command):
    _skip_python_39(command)
    query_path = tmp_path / 'query.sql'
    with pathlib.Path.open(query_path, 'w', encoding='utf-8') as f:
      f.write(self.query)
    fake_data = _SCRIPT_PATH / 'test.json'
    command = (
      f'{command} {str(query_path)} --source fake '
      f'--source.data_location={fake_data} '
      '--output console --console.format=json '
      '--loglevel ERROR'
    )
    result = subprocess.run(
      command,
      shell=True,
      check=False,
      capture_output=True,
      text=True,
    )

    assert result.returncode == 0
    assert json.loads(result.stdout) == self.expected_output

  @pytest.mark.parametrize('command', ['garf', 'grf execute'])
  def test_fake_source_from_config(self, tmp_path, command):
    _skip_python_39(command)
    query_path = tmp_path / 'query.sql'
    with pathlib.Path.open(query_path, 'w', encoding='utf-8') as f:
      f.write(self.query)
    test_config = _SCRIPT_PATH / 'test_config.yaml'
    with open(test_config, 'r', encoding='utf-8') as f:
      config_data = yaml.safe_load(f)
      original_data_location = config_data['fake']['fetcher_parameters'][
        'data_location'
      ]
      config_data['fake']['fetcher_parameters']['data_location'] = str(
        _SCRIPT_PATH / original_data_location
      )
    tmp_config = tmp_path / 'config.yaml'
    with open(tmp_config, 'w', encoding='utf-8') as f:
      yaml.dump(config_data, f, encoding='utf-8')
    command = (
      f'{command} {str(query_path)} --source fake '
      f'-c {str(tmp_config)} '
      '--loglevel ERROR'
    )
    result = subprocess.run(
      command,
      shell=True,
      check=False,
      capture_output=True,
      text=True,
    )

    assert result.returncode == 0
    assert json.loads(result.stdout) == self.expected_output

  @pytest.mark.parametrize('command', ['garf -w', 'grf workflow run -f'])
  def test_fake_source_from_workflow(self, command):
    _skip_python_39(command)
    workflow_path = _SCRIPT_PATH / 'test_workflow.yaml'
    command = f'{command} {str(workflow_path)} --loglevel ERROR'
    result = subprocess.run(
      command,
      shell=True,
      check=False,
      capture_output=True,
      text=True,
    )

    assert result.returncode == 0
    for output in result.stdout.split('\n'):
      if output:
        assert json.loads(output) == self.expected_output
