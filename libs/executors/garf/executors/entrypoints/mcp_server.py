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

"""MCP server endpoint for executing garf queries and workflows."""

from __future__ import annotations

import logging
import os
import subprocess
import sys
from typing import Literal, Optional

import fastmcp
import garf.executors
import typer
from fastmcp.server.providers.openapi import MCPType, RouteMap
from garf.executors import telemetry
from garf.executors.entrypoints import server, utils
from opentelemetry import metrics
from typing_extensions import Annotated

OTEL_SERVICE_NAME = 'garf-mcp'
ALLOWED_FOLDERS = os.getenv('GARF_ALLOWED_FOLDERS')

TransportType = Literal['stdio', 'http', 'sse', 'streamable-http']


def _get_server_info(options):
  """Collects build and version telemetry for the MCP server."""
  del options
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
      'garf.version.executors': garf.executors.version.__version__,
      'garf.version.core': garf.executors.version.core_version,
      'garf.version.io': garf.executors.version.io_version,
      'git.commit': commit_sha,
      'server.type': 'mcp',
    },
  )


executor_info = telemetry.meter.create_observable_gauge(
  'garf_mcp_info',
  callbacks=[_get_server_info],
  unit='',
  description='Build info of garf MCP executor',
)

logger = utils.init_logging(
  loglevel='INFO', logger_type='local', name=OTEL_SERVICE_NAME
)


def _redirect_stdout_logs_to_stderr() -> None:
  """Redirects stdout log handlers to stderr to preserve stdio JSON-RPC."""
  for handler in logging.getLogger().handlers:
    if (
      isinstance(handler, logging.StreamHandler)
      and handler.stream is sys.stdout
    ):
      handler.setStream(sys.stderr)


def create_mcp_server() -> fastmcp.FastMCP:
  """Creates and configures a FastMCP server from the garf FastAPI app.

  Returns:
    Configured FastMCP instance exposing garf resources and tools.
  """
  mcp_app = fastmcp.FastMCP.from_fastapi(
    app=server.app,
    name='garf',
    route_maps=[
      RouteMap(tags={'tasks'}, mcp_type=MCPType.EXCLUDE),
      RouteMap(pattern=r'^/api/execute:workflow$', mcp_type=MCPType.EXCLUDE),
      RouteMap(methods=['GET'], pattern=r'.*', mcp_type=MCPType.RESOURCE),
      RouteMap(methods=['POST'], pattern=r'.*', mcp_type=MCPType.TOOL),
    ],
  )

  @mcp_app.tool(name='execute_workflow')
  def execute_workflow(
    workflow_path: str,
    config_path: Optional[str] = None,
    selected_aliases: Optional[list[str]] = None,
    skipped_aliases: Optional[list[str]] = None,
    simulate: bool = False,
  ) -> dict[str, server.ApiExecutorResponse]:
    """Runs garf workflow till completion.

    Args:
      workflow_path: Local or remote path to the workflow YAML file.
      config_path: Optional local or remote path to the config YAML file.
      selected_aliases: Optional list of workflow step aliases to execute.
      skipped_aliases: Optional list of workflow step aliases to skip.
      simulate: Whether to simulate API responses.

    Returns:
      Mapping of workflow steps to their execution results.
    """
    return server.execute_workflow(
      workflow_file=None,
      workflow_path=workflow_path,
      config_file=None,
      config_path=config_path,
      selected_aliases=selected_aliases,
      skipped_aliases=skipped_aliases,
      simulate=simulate,
    )

  return mcp_app


mcp = create_mcp_server()
typer_app = typer.Typer()


@typer_app.command()
def main(
  transport: Annotated[
    TransportType,
    typer.Option(
      help='Transport protocol to use (stdio, http, sse, streamable-http)'
    ),
  ] = 'stdio',
  host: Annotated[
    str, typer.Option(help='Host to start the server')
  ] = '0.0.0.0',
  port: Annotated[
    int, typer.Option('--port', '-p', help='Port to start the server')
  ] = 8000,
) -> None:
  """Starts the garf MCP server."""
  if transport == 'stdio':
    _redirect_stdout_logs_to_stderr()
  if not ALLOWED_FOLDERS:
    logger.warning('GARF_ALLOWED_FOLDERS is not set')
    logger.warning(
      'Use GARF_ALLOWED_FOLDERS=location1,location2 '
      'to setup file-base write restrictions'
    )
  if transport == 'stdio':
    mcp.run(transport='stdio', show_banner=False)
  else:
    mcp.run(transport=transport, host=host, port=port)


if __name__ == '__main__':
  typer_app()
