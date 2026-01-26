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

from garf.executors import workflow_runner

_SCRIPT_PATH = pathlib.Path(__file__).parent


class TestWorkflowRunner:
  def test_run_returns_executed_step_names(self):
    runner = workflow_runner.WorkflowRunner.from_file(
      _SCRIPT_PATH / '../end-to-end/test_workflow.yaml'
    )
    results = runner.run()
    assert results == ['1-fake-test']
