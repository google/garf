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

from concurrent import futures

from garf_executors import execution_context


class Executor:
  """Defines common functionality between executors."""

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
    results = []
    with futures.ThreadPoolExecutor(max_workers=parallel_threshold) as executor:
      future_to_query = {
        executor.submit(
          self.execute,
          query,
          title,
          context,
        ): query
        for title, query in batch.items()
      }
      for future in futures.as_completed(future_to_query):
        results.append(future.result())
    return results
