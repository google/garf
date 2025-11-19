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

"""Defines common functionality between executors."""

import asyncio

from opentelemetry import trace

from garf_executors import execution_context
from garf_executors.telemetry import tracer


class Executor:
  """Defines common functionality between executors."""

  @tracer.start_as_current_span('api.execute_batch')
  def execute_batch(
    self,
    batch: dict[str, str],
    context: execution_context.ExecutionContext,
    parallel_threshold: int = 10,
  ) -> list[str]:
    """Executes batch of queries for a common context.

    Args:
      batch: Mapping between query_title and its text.
      context: Execution context.
      parallel_threshold: Number of queries to execute in parallel.

    Returns:
      Results of execution.
    """
    span = trace.get_current_span()
    span.set_attribute('api.parallel_threshold', parallel_threshold)
    return asyncio.run(
      self._run(
        batch=batch, context=context, parallel_threshold=parallel_threshold
      )
    )

  async def aexecute(
    self,
    query: str,
    title: str,
    context: execution_context.ExecutionContext,
  ) -> str:
    """Performs query execution asynchronously.

    Args:
      query: Location of the query.
      title: Name of the query.
      context: Query execution context.

    Returns:
      Result of writing the report.
    """
    return await asyncio.to_thread(self.execute, query, title, context)

  async def _run(
    self,
    batch: dict[str, str],
    context: execution_context.ExecutionContext,
    parallel_threshold: int,
  ):
    semaphore = asyncio.Semaphore(value=parallel_threshold)

    async def run_with_semaphore(fn):
      async with semaphore:
        return await fn

    tasks = [
      self.aexecute(query=query, title=title, context=context)
      for title, query in batch.items()
    ]
    return await asyncio.gather(*(run_with_semaphore(task) for task in tasks))
