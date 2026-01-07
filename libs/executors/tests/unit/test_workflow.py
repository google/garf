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
from garf_executors.workflow import Workflow


class TestWorkflow:
  data = {
    'steps': [
      {
        'fetcher': 'api',
        'queries': [
          {'path': 'example.sql'},
          {'query': {'text': 'SELECT 1', 'title': 'example2'}},
        ],
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
    ]
  }

  def test_from_file_returns_correct_context_from_data(self, tmp_path):
    tmp_workflow = tmp_path / 'workflow.yaml'
    with open(tmp_workflow, 'w', encoding='utf-8') as f:
      yaml.dump(self.data, f, encoding='utf-8')
    workflow = Workflow.from_file(tmp_workflow)
    expected_workflow = Workflow(steps=self.data.get('steps'))
    assert workflow == expected_workflow

  def test_save_returns_correct_data(self, tmp_path):
    tmp_workflow = tmp_path / 'workflow.yaml'
    workflow = Workflow(steps=self.data.get('steps'))
    workflow.save(tmp_workflow)
    with open(tmp_workflow, 'r', encoding='utf-8') as f:
      workflow_data = yaml.safe_load(f)
    assert workflow_data == self.data.get('steps')
