# Copyright 2025 Google LLC
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

"""Entrypoint for running GarfExporter.

Defines GarfExporter collectors, fetches data from API
and exposes them to Prometheus.
"""

from __future__ import annotations

import argparse
import asyncio
import contextlib
import datetime

import fastapi
import garf_exporter
import prometheus_client
import requests
import uvicorn
from garf_executors.entrypoints import utils as garf_utils
from garf_exporter import exporter_service


class GarfExporterError(Exception):
  """Base class for GarfExporter errors."""


def healthcheck(host: str, port: int) -> bool:
  """Validates that the GarfExporter export happened recently.

  Healthcheck compares the time passed since the last successful export with
  the delay between exports. If this delta if greater than 1.5 check is failed.

  Args:
    host: Hostname gaarf-exporter http server (i.e. localhost).
    port: Port gaarf-exporter http server is running (i.e. 8000).


  Returns:
    Whether or not the check is successful.
  """
  try:
    res = requests.get(f'http://{host}:{port}/metrics/').text.split('\n')
  except requests.exceptions.ConnectionError:
    return False
  last_exported = [r for r in res if 'export_completed_seconds 1' in r][
    0
  ].split(' ')[1]
  delay = None
  for result in [r for r in res if 'delay_seconds' in r]:
    _, *value = result.split(' ', maxsplit=2)
    with contextlib.suppress(ValueError):
      delay = float(value[0])
  if not delay:
    return False

  max_allowed_delta = 1.5
  is_lagged_export = (
    datetime.datetime.now().timestamp() - float(last_exported)
  ) > (max_allowed_delta * delay)

  return not is_lagged_export


app = fastapi.FastAPI(debug=False)
exporter = garf_exporter.GarfExporter()
metrics_app = prometheus_client.make_asgi_app(registry=exporter.registry)
app.mount('/metrics', metrics_app)

logger = garf_utils.init_logging(
  loglevel='INFO',
  logger_type='rich',
  name='garf-exporter',
)


async def start_metric_generation(
  request: exporter_service.GarfExporterRequest,
):
  """Exports metrics continuously from API."""
  garf_exporter_service = exporter_service.GarfExporterService(
    alias=request.source,
    source_parameters=request.source_parameters,
  )
  iterations = None
  export_metrics = True
  while export_metrics:
    garf_exporter_service.generate_metrics(request, exporter)
    if request.runtime_options.expose_type == 'pushgateway':
      prometheus_client.push_to_gateway(
        gateway=request.runtime_options.address,
        job=request.runtime_options.job_name,
        registry=exporter.registry,
      )
      export_metrics = False
    await asyncio.sleep(request.runtime_options.delay_minutes * 60)
    if iterations := iterations or request.runtime_options.iterations:
      iterations -= 1
      if iterations == 0:
        export_metrics = False


async def startup_event(
  request: exporter_service.GarfExporterRequest,
):
  """Starts async task for metrics export."""
  asyncio.create_task(start_metric_generation(request))


@app.get('/health')
def health(request: fastapi.Request):
  """Defines healthcheck endpoint for GarfExporter."""
  host = request.url.hostname
  port = request.url.port
  if not healthcheck(host, port):
    raise fastapi.HTTPException(status_code=404, detail='Not updated properly')


def main() -> None:  # noqa: D103
  parser = argparse.ArgumentParser()
  parser.add_argument('-s', '--source', dest='source')
  parser.add_argument('-c', '--config', dest='config', default=None)
  parser.add_argument('--log', '--loglevel', dest='loglevel', default='info')
  parser.add_argument(
    '--expose-type',
    dest='expose_type',
    choices=['http', 'pushgateway'],
    default='http',
  )
  parser.add_argument('--host', dest='host', default='0.0.0.0')
  parser.add_argument('--port', dest='port', type=int, default=8000)
  parser.add_argument('--logger', dest='logger', default='local')
  parser.add_argument('--iterations', dest='iterations', default=None, type=int)
  parser.add_argument('--delay-minutes', dest='delay', type=int, default=15)
  parser.add_argument('--namespace', dest='namespace', default='garf')
  parser.add_argument('--max-parallel', dest='parallel', default=None)
  parser.add_argument(
    '--fetching-timeout-seconds', dest='fetching_timeout', default=120, type=int
  )
  parser.add_argument('--collectors', dest='collectors', default='default')
  parser.add_argument('-v', '--version', dest='version', action='store_true')
  args, kwargs = parser.parse_known_args()
  cli_parameters = garf_utils.ParamsParser(['macro', 'source']).parse(kwargs)
  runtime_options = exporter_service.GarfExporterRuntimeOptions(
    expose_type=args.expose_type,
    host=args.host,
    port=args.port,
    namespace=args.namespace,
    fetching_timeout=args.fetching_timeout,
    iterations=args.iterations,
    delay_minutes=args.delay,
  )
  request = exporter_service.GarfExporterRequest(
    source=args.source,
    source_parameters=cli_parameters.get('source'),
    collectors_config=args.config,
    macros=cli_parameters.get('macro'),
    runtime_options=runtime_options,
  )
  exporter.namespace = request.runtime_options.namespace

  async def start_uvicorn():
    await startup_event(request)
    config = uvicorn.Config(
      app,
      host=request.runtime_options.host,
      port=request.runtime_options.port,
      reload=True,
    )
    server = uvicorn.Server(config)
    await server.serve()

  asyncio.run(start_uvicorn())


if __name__ == '__main__':
  main()
