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

import contextlib
import datetime
import importlib
import inspect
from collections import defaultdict
from importlib.metadata import entry_points
from typing import Any

import garf.core
import pydantic
from garf.actors import exceptions
from garf.actors.telemetry import tracer
from garf.executors.workflows import workflow


class ActionPlan(pydantic.BaseModel):
  actions: list[Any]


class ActionResult(pydantic.BaseModel):
  results: Any | None = None
  processed_at: datetime.datetime = pydantic.Field(
    description='When the media was processed',
    default_factory=datetime.datetime.utcnow,
  )


class Actor:
  def __init__(self, alias: str | None = None) -> None:
    """Initializes Actor."""
    self.alias = alias

  def act(self, report: garf.core.GarfReport, **kwargs) -> ActionResult:
    """Performs mutate action."""
    return ActionResult()

  def plan(self, report: garf.core.GarfReport, **kwargs) -> ActionPlan:
    return ActionPlan()

  @classmethod
  def from_alias(cls, actor_alias: str) -> Actor:
    return cls(alias=actor_alias)


class ActorWrapper:
  def __init__(self, actor: type[Actor]) -> None:
    self._actor = actor

  @property
  def actor(self):
    return self._actor()

  @tracer.start_as_current_span('act')
  def act(self, report: garf.core.GarfReport, **kwargs) -> ActionResult:
    """Performs mutate action."""
    results = self.actor.act(report, **kwargs)
    return ActionResult(results=results)


def load_actor(
  source: str,
  actor_name: str,
) -> ActorWrapper:
  """Locates actor with a specified name.

  Args:
    source: Location of actor.
    actor_name: Name of an actor to load.

  Returns:
    Initialized class.

  Raises:
    GarfActorError: If actor not found or cannot be loaded.
  """
  actors = entry_points(group='garf_actors')
  for actor in actors:
    if actor.name != source:
      continue
    actor_module = actor.load()
    for name, obj in inspect.getmembers(actor_module):
      if inspect.isclass(obj) and hasattr(obj, 'act') and name == actor_name:
        return ActorWrapper(actor=getattr(actor_module, name))
  raise exceptions.GarfActorError(
    f'Unsupported actor <{actor_name}>, select one of available:'
  )


def load_workflows():
  available_workflows = defaultdict(dict)
  actors = entry_points(group='garf_actor_workflows')
  for actor in actors:
    package_path_str = actor.value
    package_container = importlib.resources.files(package_path_str)
    for file_item in package_container.iterdir():
      if file_item.is_file() and file_item.name.endswith(('.yaml', '.yml')):
        workflow_info = {file_item.stem: workflow.Workflow.from_file(file_item)}
        available_workflows[actor.name].update(workflow_info)
  return available_workflows


def load_actors():
  available_actors = defaultdict(list)
  actors = entry_points(group='garf_actors')
  for actor in actors:
    with contextlib.suppress(ModuleNotFoundError):
      actor_module = actor.load()
      for name, obj in inspect.getmembers(actor_module):
        if (
          inspect.isclass(obj)
          and hasattr(obj, 'act')
          and obj.__module__ != 'garf.actors.actor'
        ):
          res = getattr(actor_module, name)
          available_actors[actor.name].append(res)
  return available_actors


def list_actors() -> list[str]:
  """Finds all available actors."""
  return [actor.name for actor in entry_points(group='garf_actors')]
