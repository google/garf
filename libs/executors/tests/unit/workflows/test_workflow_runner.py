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

import pytest
from garf.executors.workflows import workflow_runner

_SCRIPT_PATH = pathlib.Path(__file__).parent

_TEST_WORKFLOW_PATH = _SCRIPT_PATH / 'test_workflow.yaml'


class TestWorkflowRunner:
  def test_run_returns_executed_step_names(self):
    runner = workflow_runner.WorkflowRunner.from_file(_TEST_WORKFLOW_PATH)
    results = runner.run(selected_aliases=['test'])
    assert results == ['1-fake-test']

  @pytest.skip
  def test_run_parameterized_step(self):
    runner = workflow_runner.WorkflowRunner.from_file(_TEST_WORKFLOW_PATH)
    results = runner.run(selected_aliases=['test_parametrized'])
    assert results == ['1-fake-test']

  def test_compile_saves_file(self, tmp_path):
    tmp_workflow_path = tmp_path / 'workflow.yaml'
    runner = workflow_runner.WorkflowRunner.from_file(_TEST_WORKFLOW_PATH)
    result = runner.compile(tmp_workflow_path)
    assert result == f'Workflow is saved to {tmp_workflow_path}'

  def test_deploy_saves_file(self, tmp_path):
    tmp_workflow_path = tmp_path / 'workflow.yaml'
    runner = workflow_runner.WorkflowRunner.from_file(_TEST_WORKFLOW_PATH)
    result = runner.deploy(tmp_workflow_path)
    assert result == f'Workflow is saved to {tmp_workflow_path}'
