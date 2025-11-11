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

import os

from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import (
  OTLPSpanExporter,
)
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import (
  BatchSpanProcessor,
)

DEFAULT_SERVICE_NAME = 'garf'


def initialize_tracer():
  resource = Resource.create(
    {'service.name': os.getenv('OTLP_SERVICE_NAME', DEFAULT_SERVICE_NAME)}
  )

  tracer_provider = TracerProvider(resource=resource)

  if otel_endpoint := os.getenv('OTEL_EXPORTER_OTLP_ENDPOINT'):
    otlp_processor = BatchSpanProcessor(
      OTLPSpanExporter(endpoint=otel_endpoint, insecure=True)
    )
    tracer_provider.add_span_processor(otlp_processor)
  trace.set_tracer_provider(tracer_provider)
