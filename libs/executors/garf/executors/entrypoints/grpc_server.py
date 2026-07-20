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

"""gRPC endpoint for garf."""

import argparse
import logging
import os
import subprocess
import time
from concurrent import futures

import garf.executors
import grpc
from garf.executors import (
  execution_context,
  fetchers,
  garf_pb2,
  garf_pb2_grpc,
  setup,
  telemetry,
  version,
)
from garf.executors.entrypoints import utils
from garf.executors.entrypoints.tracer import (
  initialize_logger,
  initialize_meter,
  initialize_tracer,
)
from garf.executors.workflows import workflow, workflow_runner
from google.protobuf.json_format import MessageToDict
from grpc_health.v1 import health_pb2, health_pb2_grpc
from grpc_reflection.v1alpha import reflection
from opentelemetry import metrics
from opentelemetry.instrumentation.grpc import GrpcInstrumentorServer
from opentelemetry.instrumentation.logging import LoggingInstrumentor

OTEL_SERVICE_NAME = 'garf'
LoggingInstrumentor().instrument(set_logging_format=False)
grpc_server_instrumentor = GrpcInstrumentorServer()
grpc_server_instrumentor.instrument()


server_start_time = time.time()


def _get_server_info(options):
  if not (commit_sha := os.getenv('GIT_COMMIT_SHA')):
    try:
      commit_sha = (
        subprocess.check_output(['git', 'rev-parse', '--short', 'HEAD'])
        .decode('ascii')
        .strip()
      )
    except Exception:
      commit_sha = 'Unknown'

  yield metrics.Observation(
    value=1,
    attributes={
      'version_executors': garf.executors.version.__version__,
      'version_core': garf.executors.version.core_version,
      'version_io': garf.executors.version.io_version,
      'git_commit': commit_sha,
      'server_type': 'grpc',
    },
  )


executor_info = telemetry.meter.create_observable_gauge(
  'garf_info',
  callbacks=[_get_server_info],
  unit='',
  description='Build info of garf executor',
)


class GarfService(garf_pb2_grpc.GarfService):
  def Execute(self, request, context):
    telemetry.executor_requested_counter.add(
      1, attributes={'executor.source': request.source}
    )
    query_executor = setup.setup_executor(
      request.source, request.context.fetcher_parameters
    )
    result = query_executor.execute(
      query=request.query,
      title=request.title,
      context=execution_context.ExecutionContext(
        **MessageToDict(request.context, preserving_proto_field_name=True)
      ),
    )
    return garf_pb2.ExecuteResponse(results=[result])

  def ExecuteBatch(self, request, context):
    n_queries = len(request.batch)
    telemetry.executor_requested_counter.add(
      n_queries, attributes={'executor.source': request.source}
    )
    query_executor = setup.setup_executor(
      request.source, request.context.fetcher_parameters
    )
    batch = {query.title: query.text for query in request.batch}
    results = query_executor.execute_batch(
      batch=batch,
      context=execution_context.ExecutionContext(
        **MessageToDict(request.context, preserving_proto_field_name=True)
      ),
    )
    return garf_pb2.ExecuteResponse(results=results)

  def Fetch(self, request, context):
    query_executor = setup.setup_executor(
      request.source, request.context.fetcher_parameters
    )
    query_args = execution_context.ExecutionContext(
      **MessageToDict(request.context, preserving_proto_field_name=True)
    ).query_parameters
    result = query_executor.fetcher.fetch(
      query_specification=request.query,
      title=request.title,
      args=query_args,
    )
    return garf_pb2.FetchResponse(
      columns=result.column_names, rows=result.to_list(row_type='dict')
    )

  def ExecuteWorkflow(self, request, context):
    execution_workflow = workflow.Workflow(
      **MessageToDict(request.workflow, preserving_proto_field_name=True)
    )
    telemetry.workflow_requested.add(
      1, attributes=execution_workflow.attributes
    )
    runner = workflow_runner.WorkflowRunner(
      execution_workflow=execution_workflow
    )
    results = runner.run()
    return garf_pb2.ExecuteWorkflowResponse(results=results)

  def GetVersion(self, request, context):
    return garf_pb2.GarfVersion(version=version.__version__)

  def GetInfo(self, request, context):
    return garf_pb2.GarfInfo(
      executors_version=version.__version__,
      core_version=version.core_version,
      io_version=version.io_version,
    )

  def ListFetchers(self, request, context):
    return garf_pb2.ListFetchersResponse(
      results=[
        garf_pb2.FetcherInfo(name=name, version=fetcher.version)
        for name, fetcher in fetchers.get_all_report_fetchers().items()
      ]
    )

  def ListExecutors(self, request, context):
    return garf_pb2.ListExecutorsResponse(results=setup.available_executors())

  def Check(self, request, context):
    return health_pb2.HealthCheckResponse(
      status=health_pb2.HealthCheckResponse.SERVING
    )

  def Watch(self, request, context):
    return health_pb2.HealthCheckResponse(
      status=health_pb2.HealthCheckResponse.UNIMPLEMENTED
    )


if __name__ == '__main__':
  parser = argparse.ArgumentParser()
  parser.add_argument('--port', dest='port', default=50051, type=int)
  parser.add_argument(
    '--parallel-threshold', dest='parallel_threshold', default=10, type=int
  )
  args, _ = parser.parse_known_args()
  otel_service_name = os.getenv('OTEL_SERVICE_NAME', OTEL_SERVICE_NAME)
  initialize_tracer(otel_service_name)
  meter = initialize_meter(otel_service_name)
  logger = utils.init_logging(
    loglevel='INFO',
    logger_type='local',
    name=otel_service_name,
  )
  logger.addHandler(initialize_logger())

  server = grpc.server(
    futures.ThreadPoolExecutor(max_workers=args.parallel_threshold),
  )

  service = GarfService()
  garf_pb2_grpc.add_GarfServiceServicer_to_server(service, server)
  health_pb2_grpc.add_HealthServicer_to_server(service, server)
  SERVICE_NAMES = (
    garf_pb2.DESCRIPTOR.services_by_name['GarfService'].full_name,
    reflection.SERVICE_NAME,
  )
  reflection.enable_server_reflection(SERVICE_NAMES, server)
  server.add_insecure_port(f'[::]:{args.port}')
  server.start()
  logging.info('Garf service started, listening on port %d', args.port)
  server.wait_for_termination()
