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
from __future__ import annotations

import pathlib
from typing import Any, Literal

import pydantic
from garf.actors import actor, exceptions
from garf.actors.telemetry import tracer
from garf.executors import utils
from garf.executors.workflows import workflow, workflow_runner
from opentelemetry import trace

_SCRIPT_PATH = pathlib.Path(__file__).parent


class GarfActorRunError(exceptions.GarfActorError):
  """Garf actor exception for workflows."""


def validate(actor_workflow: workflow.Workflow):
  last_step = actor_workflow.steps[-1]
  if alias := (last_step.alias) != 'evaluation':
    raise GarfActorRunError(f'Final step should be evaluation, got {alias}')
  if (n_queries := len(last_step.queries)) > 1:
    raise GarfActorRunError(
      f'Expected a single query as an evaluation, got {n_queries} instead'
    )


class ActorInput(pydantic.BaseModel):
  name: str = 'fake'
  source: str = 'fake'
  type: Literal['query', 'workflow', 'workflow_name', 'workflow_file'] = (
    'workflow_name'
  )
  data: Any = pydantic.Field(default_factory=dict)
  context: Any = pydantic.Field(default_factory=dict)


class GarfActorRequest(pydantic.BaseModel):
  input: ActorInput
  rule: str | None = None
  actor: str | None = None
  actor_parameters: dict[str, Any] = pydantic.Field(default_factory=dict)

  @tracer.start_as_current_span('fetch')
  def fetch(self, workflow_obj=None):
    context = {}
    if self.rule:
      context = {'template': {'filters': self.rule}}
    if self.input.context:
      context = utils.merge_dicts(context, self.input.context)
    if self.actor_parameters:
      context = utils.merge_dicts(context, {'template': self.actor_parameters})

    if workflow_obj:
      workflow_data = workflow_obj.model_dump()
      workflow_data.update({'context': context})
      actor_workflow = workflow.Workflow(**workflow_data)
    elif self.input.type == 'workflow_name':
      actor_workflow = workflow.Workflow.from_file(
        path=(
          _SCRIPT_PATH
          / f'actors/{self.input.source}/workflows/{self.input.name}.yaml'
        ),
        context=context,
      )
    elif self.input.type == 'workflow_file':
      actor_workflow = workflow.Workflow.from_file(
        path=self.input.data,
        context=context,
      )
    elif self.input.type == 'workflow':
      workflow_data = self.input.data
      workflow_data.update({'context': context})
      actor_workflow = workflow.Workflow(**workflow_data)
    elif self.input.type == 'query':
      workflow_data = {
        'steps': [
          {
            'fetcher': self.input.source,
            'alias': 'task',
            'writer': [
              'sqldb',
            ],
            'queries': [
              {'text': self.input.data, 'title': 'task'},
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
        ]
      }
      workflow_data.update({'context': context})
      actor_workflow = workflow.Workflow(**workflow_data)

    validate(actor_workflow)

    results = workflow_runner.WorkflowRunner(actor_workflow).run(
      enable_cache=True
    )
    evaluator_key = list(results.keys())[-1]
    return results.get(evaluator_key).get('evaluation')

  # @tracer.start_as_current_span('notify')
  # def notify(
  #   self,
  #   report: garf.core.GarfReport,
  #   notification_channel: notifications_channel.NotificationChannel,
  # ):
  #   notification_channel.send(report)

  @tracer.start_as_current_span('play')
  def play(self, workflow=None):
    span = trace.get_current_span()
    if self.actor:
      actor_client = actor.load_actor(
        source=self.input.source, actor_name=self.actor
      )
      span.set_attribute('garf.actor.class', actor_client.actor.__name__)
    report = self.fetch(workflow)
    if self.actor:
      action_result = actor_client.act(report, workflow_name=self.input.name)
    return action_result
    # self.notify(report, notification_channel=notifications_channel.Console())
