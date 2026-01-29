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
from garf.executors.workflows.workflow import Workflow


class TestWorkflow:
  data = {
    'steps': [
      {
        'fetcher': 'api',
        'queries': [
          {'folder': 'queries'},
          {'path': 'example.sql'},
          {'query': {'text': 'SELECT 1', 'title': 'example2'}},
        ],
        'query_parameters': {
          'macro': {
            'start_date': '2025-01-01',
            'end_date': '2025-12-31',
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
    assert workflow_data == self.data

  def test_init_with_context(self):
    new_start_date = '2026-01-01'
    new_cohort = '2'
    new_ids = [4, 5, 6]
    new_folder = '/app'
    workflow = Workflow(
      steps=self.data.get('steps'),
      context={
        'query_parameters': {
          'macro': {'start_date': new_start_date},
          'template': {'cohorts': new_cohort},
        },
        'fetcher_parameters': {
          'id': new_ids,
        },
        'writer_parameters': {
          'destination_folder': new_folder,
        },
      },
    )

    step = workflow.steps[0]
    assert step.query_parameters.macro.get('start_date') == new_start_date
    assert step.query_parameters.macro.get('end_date') == '2025-12-31'
    assert step.query_parameters.template.get('cohorts') == new_cohort
    assert step.fetcher_parameters.get('id') == new_ids
    assert step.writer_parameters.get('destination_folder') == new_folder
