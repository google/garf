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
from concurrent import futures

import grpc
from google.protobuf.json_format import MessageToDict
from grpc_reflection.v1alpha import reflection

import garf_executors
from garf_executors import garf_pb2, garf_pb2_grpc
from garf_executors.entrypoints.tracer import initialize_tracer


class GarfService(garf_pb2_grpc.GarfService):
  def Execute(self, request, context):
    query_executor = garf_executors.setup_executor(
      request.source, request.context.fetcher_parameters
    )
    execution_context = garf_executors.execution_context.ExecutionContext(
      **MessageToDict(request.context, preserving_proto_field_name=True)
    )
    result = query_executor.execute(
      query=request.query,
      title=request.title,
      context=execution_context,
    )
    return garf_pb2.ExecuteResponse(results=[result])


if __name__ == '__main__':
  parser = argparse.ArgumentParser()
  parser.add_argument('--port', dest='port', default=50051, type=int)
  parser.add_argument(
    '--parallel-threshold', dest='parallel_threshold', default=10, type=int
  )
  args, _ = parser.parse_known_args()
  initialize_tracer()
  server = grpc.server(
    futures.ThreadPoolExecutor(max_workers=args.parallel_threshold)
  )

  service = GarfService()
  garf_pb2_grpc.add_GarfServiceServicer_to_server(service, server)
  SERVICE_NAMES = (
    garf_pb2.DESCRIPTOR.services_by_name['GarfService'].full_name,
    reflection.SERVICE_NAME,
  )
  reflection.enable_server_reflection(SERVICE_NAMES, server)
  server.add_insecure_port(f'[::]:{args.port}')
  server.start()
  logging.info('Garf service started, listening on port %d', 50051)
  server.wait_for_termination()
