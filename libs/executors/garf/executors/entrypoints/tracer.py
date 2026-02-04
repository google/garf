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

"""Opentelemetry initialization functions."""

import os

from opentelemetry import metrics, trace
from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import (
  OTLPMetricExporter,
)
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import (
  OTLPSpanExporter,
)
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import (
  PeriodicExportingMetricReader,
)
from opentelemetry.sdk.resources import SERVICE_NAME, Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

DEFAULT_SERVICE_NAME = 'garf'


def initialize_tracer():
  resource = Resource.create(
    {SERVICE_NAME: os.getenv('OTLP_SERVICE_NAME', DEFAULT_SERVICE_NAME)}
  )

  tracer_provider = TracerProvider(resource=resource)

  if otel_endpoint := os.getenv('OTEL_EXPORTER_OTLP_ENDPOINT'):
    if gcp_project_id := os.getenv('OTEL_EXPORTER_GCP_PROJECT_ID'):
      try:
        from opentelemetry.exporter.cloud_trace import CloudTraceSpanExporter
      except ImportError as e:
        raise ImportError(
          'Please install garf-executors with GCP support '
          '- `pip install garf-executors[gcp]`'
        ) from e

      cloud_span_processor = BatchSpanProcessor(
        CloudTraceSpanExporter(project_id=gcp_project_id, resource_regexp='*')
      )
      tracer_provider.add_span_processor(cloud_span_processor)
    else:
      otlp_processor = BatchSpanProcessor(
        OTLPSpanExporter(endpoint=otel_endpoint, insecure=True)
      )
      tracer_provider.add_span_processor(otlp_processor)

  trace.set_tracer_provider(tracer_provider)


def initialize_meter():
  resource = Resource.create(
    {SERVICE_NAME: os.getenv('OTLP_SERVICE_NAME', DEFAULT_SERVICE_NAME)}
  )
  meter_provider = MeterProvider(resource=resource)

  if otel_endpoint := os.getenv('OTEL_EXPORTER_OTLP_ENDPOINT'):
    if gcp_project_id := os.getenv('OTEL_EXPORTER_GCP_PROJECT_ID'):
      try:
        from opentelemetry.exporter.cloud_monitoring import (
          CloudMonitoringMetricsExporter,
        )
      except ImportError as e:
        raise ImportError(
          'Please install garf-executors with GCP support '
          '- `pip install garf-executors[gcp]`'
        ) from e

      metric_exporter = CloudMonitoringMetricsExporter(
        project_id=gcp_project_id, resource_regexp='*'
      )
    else:
      metric_exporter = OTLPMetricExporter(
        endpoint=f'{otel_endpoint}/v1/metrics'
      )
    metric_reader = PeriodicExportingMetricReader(metric_exporter)
    meter_provider = MeterProvider(
      resource=resource, metric_readers=[metric_reader]
    )
  else:
    meter_provider = MeterProvider(resource=resource)
  metrics.set_meter_provider(meter_provider)
  return meter_provider
