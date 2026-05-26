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

# pylint: disable=C0330, g-bad-import-order, g-multiple-import
from opentelemetry import metrics, trace

tracer = trace.get_tracer(
  instrumenting_module_name='garf.executors',
)
meter = metrics.get_meter('garf.executors')

executor_info = meter.create_gauge(
  'garf_info',
  unit='',
  description='Build info of garf executor',
)

executor_started_seconds = meter.create_gauge(
  'garf_executor_started_seconds',
  unit='s',
  description='Timestamp when process started',
)

executor_active_executions = meter.create_up_down_counter(
  'garf_execute_active',
  unit='1',
  description='Counts number of active executions',
)
executor_requested_counter = meter.create_counter(
  'garf_execute_requested_total',
  unit='1',
  description='Counts number of executor invocations requested',
)
executor_counter = meter.create_counter(
  'garf_execute_total',
  unit='1',
  description='Counts number of executor invocations',
)

executor_error_counter = meter.create_counter(
  'garf_execute_errors_total',
  unit='1',
  description='Counts number of executor failures',
)

executor_histogram = meter.create_histogram(
  'garf_execute_duration_seconds',
  unit='s',
  description='Measures execution duration in seconds',
)
write_histogram = meter.create_histogram(
  'garf_write_duration_seconds',
  unit='s',
  description='Measures report writes duration in seconds',
)

executor_active_workflows = meter.create_up_down_counter(
  'garf_workflow_active',
  unit='1',
  description='Counts number of active workflows',
)
workflow_requested = meter.create_counter(
  'garf_workflow_run_requested_total',
  unit='1',
  description='Counts number of workflow run was requested',
)
workflow_counter = meter.create_counter(
  'garf_workflow_run_total',
  unit='1',
  description='Counts number of workflow runs',
)

workflow_histogram = meter.create_histogram(
  'garf_workflow_run_duration_seconds',
  unit='s',
  description='Measures workflow run duration in seconds',
)

workflow_error_counter = meter.create_counter(
  'garf_workflow_run_errors_total',
  unit='1',
  description='Counts number of workflow failures',
)

workflow_step_counter = meter.create_counter(
  'garf_workflow_step_run_total',
  unit='1',
  description='Counts number of runs of workflow step',
)

workflow_step_histogram = meter.create_histogram(
  'garf_workflow_step_run_duration_seconds',
  unit='s',
  description='Measures run duration in seconds of workflow step',
)

workflow_step_error_counter = meter.create_counter(
  'garf_workflow_step_run_errors_total',
  unit='1',
  description='Counts number of workflow step failures',
)
