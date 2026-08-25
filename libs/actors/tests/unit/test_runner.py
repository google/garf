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
import yaml
from garf.actors import actor, runner


class TestRunner:
  def test_play_with_builtin_workflow_name(self):
    test_runner = runner.GarfActorRequest(
      input={'name': 'fake', 'type': 'workflow_name'},
      rule='value > -1',
      actor='Faker',
    )
    result = test_runner.play()
    expected_result = actor.ActionResult(
      results=None, processed_at=result.processed_at
    )

    assert result == expected_result

  def test_play_with_custom_query(self):
    test_runner = runner.GarfActorRequest(
      input={
        'name': 'fake',
        'type': 'query',
        'data': 'SELECT metric.int AS field FROM fake',
        'context': {
          'fake': {'n_rows': 10},
          'sqldb': {'connection_string': 'sqlite:////tmp/garf-dev.db'},
        },
      },
      rule='field > -1',
      actor='Faker',
    )
    result = test_runner.play()
    expected_result = actor.ActionResult(
      results=None, processed_at=result.processed_at
    )

    assert result == expected_result

  def test_play_with_custom_workflow(self):
    test_runner = runner.GarfActorRequest(
      input={
        'name': 'fake',
        'type': 'workflow',
        'data': {
          'name': 'test_workflow',
          'steps': [
            {
              'fetcher': 'fake',
              'alias': 'task',
              'writer': [
                'sqldb',
              ],
              'queries': [
                {
                  'text': 'SELECT metric.int AS field FROM fake',
                  'title': 'task',
                },
              ],
            },
            {
              'fetcher': 'sqldb',
              'alias': 'evaluation',
              'queries': [
                {
                  'text': 'SELECT * FROM task WHERE {{ filters }}',
                  'title': 'evaluation',
                },
              ],
              'query_parameters': {
                'template': {
                  'filters': 'TRUE',
                }
              },
            },
          ],
        },
        'context': {
          'fake': {'n_rows': 10},
          'sqldb': {'connection_string': 'sqlite:////tmp/garf-dev.db'},
        },
      },
      rule='field > -1',
      actor='Faker',
    )
    result = test_runner.play()
    expected_result = actor.ActionResult(
      results=None, processed_at=result.processed_at
    )

    assert result == expected_result

  def test_play_with_custom_workflow_file(self, tmp_path):
    workflow_data = {
      'name': 'test_workflow',
      'steps': [
        {
          'fetcher': 'fake',
          'alias': 'task',
          'writer': [
            'sqldb',
          ],
          'queries': [
            {
              'text': 'SELECT metric.int AS field FROM fake',
              'title': 'task',
            },
          ],
        },
        {
          'fetcher': 'sqldb',
          'alias': 'evaluation',
          'queries': [
            {
              'text': 'SELECT * FROM task WHERE {{ filters }}',
              'title': 'evaluation',
            },
          ],
          'query_parameters': {
            'template': {
              'filters': 'TRUE',
            }
          },
        },
      ],
    }

    tmp_workflow = tmp_path / 'workflow.yaml'
    with open(tmp_workflow, 'w', encoding='utf-8') as f:
      yaml.dump(workflow_data, f, encoding='utf-8')
    test_runner = runner.GarfActorRequest(
      input={
        'name': 'fake',
        'type': 'workflow_file',
        'data': str(tmp_workflow),
        'context': {
          'fake': {'n_rows': 10},
          'sqldb': {'connection_string': 'sqlite:////tmp/garf-dev.db'},
        },
      },
      rule='field > -1',
      actor='Faker',
    )
    result = test_runner.play()
    expected_result = actor.ActionResult(
      results=None, processed_at=result.processed_at
    )

    assert result == expected_result
