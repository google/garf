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
from garf.executors.entrypoints import grpc_interceptors, utils
from garf.executors.entrypoints.tracer import (
  initialize_logger,
  initialize_meter,
  initialize_tracer,
)
from garf.executors.workflows import workflow, workflow_runner
from garf.io import formatter, reader
from google.protobuf.json_format import MessageToDict
from grpc_health.v1 import health_pb2
from grpc_reflection.v1alpha import reflection
from opentelemetry import metrics

OTEL_SERVICE_NAME = 'garf'
CACHE_ENABLED = os.getenv('GARF_CACHE_LOCATION')

server_start_time = time.time()


class GarfGrpcServerError(Exception):
  """Failure to find credentials."""


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
      source=request.source,
      fetcher_parameters=request.context.fetcher_parameters,
      enable_cache=bool(request.cache_options.enable_cache)
      if CACHE_ENABLED
      else False,
      cache_ttl_seconds=request.cache_options.cache_ttl_seconds,
      simulate=request.simulate,
      writers=request.context.writers or request.context.writer,
      writer_parameters=MessageToDict(
        request.context.writer_parameters, preserving_proto_field_name=True
      ),
    )
    if query := request.query_path:
      title = formatter.format_extension(query)
      text = reader.FileReader().read(query)
    else:
      title, text = (
        request.query_definition.title,
        request.query_definition.text,
      )

    result = query_executor.execute(
      query=text,
      title=title,
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
      source=request.source,
      fetcher_parameters=request.context.fetcher_parameters,
      enable_cache=bool(request.cache_options.enable_cache)
      if CACHE_ENABLED
      else False,
      cache_ttl_seconds=request.cache_options.cache_ttl_seconds,
      simulate=request.simulate,
      writers=request.context.writers or request.context.writer,
      writer_parameters=MessageToDict(
        request.context.writer_parameters, preserving_proto_field_name=True
      ),
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
      source=request.source,
      fetcher_parameters=request.context.fetcher_parameters,
      enable_cache=bool(request.cache_options.enable_cache)
      if CACHE_ENABLED
      else False,
      cache_ttl_seconds=request.cache_options.cache_ttl_seconds,
      simulate=request.simulate,
    )
    query_args = execution_context.ExecutionContext(
      **MessageToDict(request.context, preserving_proto_field_name=True)
    ).query_parameters
    if hasattr(query_executor, 'fetcher'):
      result = query_executor.fetcher.fetch(
        query_specification=request.query,
        title=request.title,
        args=query_args,
      )
    else:
      result = query_executor.fetch(
        query_specification=request.query,
        title=request.title,
        args=query_args,
      )
    return garf_pb2.FetchResponse(
      columns=result.column_names, rows=result.to_list(row_type='dict')
    )

  def ExecuteWorkflow(self, request, context):
    execution_workflow = workflow.Workflow(
      **MessageToDict(request.workflow, preserving_proto_field_name=True),
      context=MessageToDict(request.context, preserving_proto_field_name=True),
      execution_config=MessageToDict(
        request.config, preserving_proto_field_name=True
      ),
    )
    telemetry.workflow_requested.add(
      1, attributes=execution_workflow.attributes
    )
    runner = workflow_runner.WorkflowRunner(
      execution_workflow=execution_workflow
    )
    results = runner.run(
      selected_aliases=request.selected_aliases,
      skipped_aliases=request.skipped_aliases,
      simulate=request.simulate,
      enable_cache=request.cache_options.enable_cache,
      cache_ttl_seconds=request.cache_options.cache_ttl_seconds,
    )
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


def _read_server_cert_files():
  cert_path = os.getenv('GRPC_SERVER_CERT_PATH', '/certs/server.crt')
  key_path = os.getenv('GRPC_SERVER_KEY_PATH', '/certs/server.key')
  if cert_path and key_path:
    try:
      with open(cert_path, 'rb') as f:
        cert_bytes = f.read()
      with open(key_path, 'rb') as f:
        key_bytes = f.read()
      return (cert_bytes, key_bytes)
    except FileNotFoundError as e:
      raise GarfGrpcServerError from e
  raise GarfGrpcServerError


def init_server(
  max_workers: int, port: int = 50051, enable_reflection: bool = False
):
  interceptors = []
  if auth_token := os.getenv('GRPC_AUTH_TOKEN'):
    interceptors.append(
      grpc_interceptors.TokenAuthInterceptor(expected_token=auth_token)
    )
  if jwt_public_key := os.getenv('GRPC_JWT_PUBLIC_KEY'):
    interceptors.append(
      grpc_interceptors.JWTAuthInterceptor(
        public_key=jwt_public_key,
        expected_audience=os.getenv('GRPC_JWT_EXPECTED_AUDIENCE'),
        expected_issuer=os.getenv('GRPC_JWT_EXPECTED_ISSUER'),
      )
    )

  server = grpc.server(
    futures.ThreadPoolExecutor(max_workers=max_workers),
    interceptors=interceptors,
  )

  service = GarfService()
  garf_pb2_grpc.add_GarfServiceServicer_to_server(service, server)
  try:
    server_cert, server_key = _read_server_cert_files()
    server_credentials = grpc.ssl_server_credentials(
      private_key_certificate_chain_pairs=[(server_key, server_cert)],
    )
    server.add_secure_port(f'127.0.0.1:{port}', server_credentials)
  except GarfGrpcServerError:
    server.add_insecure_port(f'127.0.0.1:{port}')
  if enable_reflection:
    service_names = (
      garf_pb2.DESCRIPTOR.services_by_name['GarfService'].full_name,
      reflection.SERVICE_NAME,
    )
    reflection.enable_server_reflection(service_names, server)
  return server


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

  server = init_server(
    max_workers=args.parallel_threshold,
    port=args.port,
    enable_reflection=os.getenv('GARF_GRPC_SERVER_ENABLE_REFLECTION'),
  )
  server.start()
  server.wait_for_termination()
