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
import pathlib

import yaml
from garf.executors.workflows import workflow_runner
from garf.executors.workflows.workflow import Workflow, WorkflowEdge

_SCRIPT_PATH = pathlib.Path(__file__).parent

_TEST_WORKFLOW_PATH = _SCRIPT_PATH / 'test_workflow.yaml'


class TestWorkflowRunner:
  def test_run_returns_executed_step_names(self):
    workflow = Workflow.from_file(_TEST_WORKFLOW_PATH)
    runner = workflow_runner.WorkflowRunner(execution_workflow=workflow)
    results = runner.run()
    assert list(results.keys()) == ['1-fake-test', '2-fake-test2']

  def test_run_includes_aliases(self):
    workflow = Workflow.from_file(_TEST_WORKFLOW_PATH)
    runner = workflow_runner.WorkflowRunner(execution_workflow=workflow)
    results = runner.run(selected_aliases=['test'])
    assert list(results.keys()) == ['1-fake-test']

  def test_run_includes_aliases_regexp(self):
    workflow = Workflow.from_file(_TEST_WORKFLOW_PATH)
    runner = workflow_runner.WorkflowRunner(execution_workflow=workflow)
    results = runner.run(selected_aliases=['test*', 'non-existing*'])
    assert list(results.keys()) == ['1-fake-test', '2-fake-test2']

  def test_run_excludes_aliases(self):
    workflow = Workflow.from_file(_TEST_WORKFLOW_PATH)
    runner = workflow_runner.WorkflowRunner(execution_workflow=workflow)
    results = runner.run(skipped_aliases=['test2', 'not-existing'])
    assert list(results.keys()) == ['1-fake-test']

  def test_run_excludes_aliases_regexp(self):
    workflow = Workflow.from_file(_TEST_WORKFLOW_PATH)
    runner = workflow_runner.WorkflowRunner(execution_workflow=workflow)
    results = runner.run(skipped_aliases=['test*', 'not-existing*'])
    assert not results

  def test_compile_saves_file(self, tmp_path):
    tmp_workflow_path = tmp_path / 'workflow.yaml'
    workflow = Workflow.from_file(_TEST_WORKFLOW_PATH)
    runner = workflow_runner.WorkflowRunner(execution_workflow=workflow)
    result = runner.compile(tmp_workflow_path)
    assert result == f'Workflow is saved to {tmp_workflow_path}'

  def test_deploy_saves_file(self, tmp_path):
    tmp_workflow_path = tmp_path / 'workflow.yaml'
    runner = workflow_runner.WorkflowRunner.from_file(_TEST_WORKFLOW_PATH)
    result = runner.deploy(tmp_workflow_path)
    assert result == f'Workflow is saved to {tmp_workflow_path}'

  def test_run_with_parallel_steps(self, tmp_path):
    data = {
      'steps': [
        {
          'fetcher': 'sqldb',
          'alias': 'sequential',
          'queries': [
            {'query': {'text': 'SELECT 1', 'title': 'example2'}},
          ],
        },
        {
          'parallel': [
            {
              'fetcher': 'sqldb',
              'alias': 'parallel_1',
              'queries': [
                {'query': {'text': 'SELECT 1', 'title': 'example2'}},
              ],
            },
            {
              'fetcher': 'sqldb',
              'alias': 'parallel_2',
              'queries': [
                {'query': {'text': 'SELECT 1', 'title': 'example2'}},
              ],
            },
          ]
        },
      ],
      'name': 'test workflow',
    }
    tmp_workflow = tmp_path / 'workflow.yaml'
    with open(tmp_workflow, 'w', encoding='utf-8') as f:
      yaml.dump(data, f, encoding='utf-8')
    workflow = Workflow.from_file(tmp_workflow)
    runner = workflow_runner.WorkflowRunner(execution_workflow=workflow)
    results = runner.run()
    assert set(results.keys()) == {
      '1-sqldb-sequential',
      '2-sqldb-parallel_1',
      '2-sqldb-parallel_2',
    }
