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
"""Defines `grf` CLI utility."""

from __future__ import annotations

import enum
import pathlib
import sys
from typing import Optional

import garf.executors
import requests
import typer
from garf.executors import exceptions, setup
from garf.executors.config import Config
from garf.executors.entrypoints import utils
from garf.executors.entrypoints.tracer import (
  initialize_logger,
  initialize_tracer,
)
from garf.executors.telemetry import tracer
from garf.executors.workflows import workflow, workflow_runner
from garf.io import reader, writer
from opentelemetry import trace
from opentelemetry.instrumentation.logging import LoggingInstrumentor
from opentelemetry.trace.propagation.tracecontext import (
  TraceContextTextMapPropagator,
)
from rich.console import Console
from rich.table import Table
from typing_extensions import Annotated

LoggingInstrumentor().instrument(set_logging_format=False)
console = Console()


FetcherEnum = enum.Enum(
  'FetcherEnum',
  ((f, f) for f in sorted(setup.find_executors())),
)

initialize_tracer()
typer_app = typer.Typer(
  help='Garf\n\nCall APIs with SQL in your terminal', rich_markup_mode='rich'
)
workflow_app = typer.Typer(help='Execute workflow')
typer_app.add_typer(
  workflow_app,
  name='workflow',
)

EnableCache = Annotated[
  bool,
  typer.Option(
    help='Whether to store results of execution in a cache',
  ),
]
Simulate = Annotated[
  bool,
  typer.Option(
    help='Whether to simulate results',
  ),
]
CacheTTL = Annotated[
  int,
  typer.Option(
    help='TTL of cache results in seconds',
  ),
]
Output = Annotated[
  writer.WriterOption,
  typer.Option(help='Where to write data'),
]
ParallelThreshold = Annotated[
  int,
  typer.Option(
    help='Number of parallel queries to run',
  ),
]
Logger = Annotated[
  utils.LoggerEnum,
  typer.Option(
    help='Type of logger',
  ),
]
LogLevel = Annotated[
  str,
  typer.Option(
    help='Level of logging',
  ),
]
LogName = Annotated[
  str,
  typer.Option(
    help='Name of logger',
  ),
]


def _init_runner(
  file, context=None, config=None
) -> workflow_runner.WorkflowRunner:
  wf_parent = pathlib.Path.cwd() / pathlib.Path(file).parent
  execution_workflow = workflow.Workflow.from_file(
    path=file, context=context, config_file=config
  )
  return workflow_runner.WorkflowRunner(
    execution_workflow=execution_workflow, wf_parent=wf_parent
  )


@typer_app.command(
  context_settings={'allow_extra_args': True, 'ignore_unknown_options': True},
)
@tracer.start_as_current_span('garf.cli.execute')
def execute(
  source: Annotated[FetcherEnum, typer.Option(help='API alias')],
  queries: Annotated[
    list[str], typer.Argument(help='One or several query files')
  ],
  config: Annotated[
    Optional[str],
    typer.Option('--config', '-c', help='Yaml file with parameters'),
  ] = None,
  input: Annotated[
    reader.InputEnum,
    typer.Option(help='Where to get queries from'),
  ] = 'file',
  output: Output = 'console',
  parallel_threshold: ParallelThreshold = 10,
  loglevel: LogLevel = 'INFO',
  logger: Logger = 'rich',
  log_name: LogName = 'garf',
  enable_cache: EnableCache = False,
  cache_ttl_seconds: CacheTTL = 3600,
  simulate: Simulate = False,
  macro_expansion: Annotated[
    bool,
    typer.Option(
      help='Whether to perform macro expansion in the queries',
    ),
  ] = True,
  server_url: Annotated[
    str | None, typer.Option(help='Address of garf server in HOST:PORT format')
  ] = None,
) -> None:
  """Runs queries."""
  span = trace.get_current_span()
  command_args = ' '.join(sys.argv[1:])
  span.set_attribute('cli.command', f'grf {command_args}')
  garf_logger = utils.init_logging(
    loglevel=loglevel.upper(), logger_type=logger, name=log_name
  )
  garf_logger.addHandler(initialize_logger())

  found_queries = []
  parameters = []
  for query in queries:
    if query.startswith('--'):
      parameters.append(query)
    else:
      found_queries.append(query)
  if not found_queries:
    garf_logger.error('Please provide one or more queries to run')
    raise exceptions.GarfExecutorError(
      'Please provide one or more queries to run'
    )
  if not found_queries:
    garf_logger.error('Please provide one or more queries to run')
    raise exceptions.GarfExecutorError(
      'Please provide one or more queries to run'
    )
  source = source.value
  input = input.value
  output = output.value
  reader_client = reader.create_reader(input)
  param_types = ['source', 'macro', 'template']
  outputs = output.split(',')
  extra_parameters = utils.ParamsParser([*param_types, *outputs]).parse_all(
    parameters
  )
  source_parameters = extra_parameters.get('source', {})
  source_parameters.update(extra_parameters.get(source, {}))
  writer_parameters = {}
  for o in outputs:
    writer_parameters.update(extra_parameters.get(o))
  context = garf.executors.execution_context.ExecutionContext(
    query_parameters={
      'macro': extra_parameters.get('macro'),
      'template': extra_parameters.get('template'),
      'macro_expansion': macro_expansion,
    },
    writer=outputs,
    writer_parameters=writer_parameters,
    fetcher_parameters=source_parameters,
  )

  if config:
    garf_logger.info('Running queries with config: %s', config)
    execution_config = Config.from_file(config).expand()
    if not (context := execution_config.sources.get(source)):
      raise exceptions.GarfExecutorError(
        f'No execution context found for source {source} in {config}'
      )
  parallel_queries = parallel_threshold > 1
  with tracer.start_as_current_span('read_queries'):
    batch = {query: reader_client.read(query) for query in found_queries}
  if server_url:
    rest_context = context.model_dump()
    if rest_context.get('writer') == ['console']:
      del rest_context['writer']
    headers = {}
    TraceContextTextMapPropagator().inject(headers)
    if parallel_queries and len(batch) > 1:
      endpoint = f'{server_url}/api/execute:batch'
      request = {
        'batch': batch,
        'source': source,
        'context': rest_context,
      }
      try:
        response = requests.post(url=endpoint, json=request, headers=headers)
        response.raise_for_status()
      except requests.exceptions.HTTPError as e:
        raise exceptions.GarfExecutorError(
          f'Server error: {e.response.status_code} - {e.response.json()}'
        ) from e

      with tracer.start_as_current_span('parse_results batch'):
        typer.secho(response.json().get('results'))
    else:
      endpoint = f'{server_url}/api/execute'
      for title, text in batch.items():
        request = {
          'source': source,
          'title': title,
          'query': text,
          'context': rest_context,
        }
        try:
          response = requests.post(url=endpoint, json=request, headers=headers)
          response.raise_for_status()
        except requests.exceptions.HTTPError as e:
          raise exceptions.GarfExecutorError(
            f'Server error: {e.response.status_code} - {e.response.json()}'
          ) from e
      with tracer.start_as_current_span(f'parse_results {title}'):
        typer.secho(response.json().get('results'))
  else:
    query_executor = setup.setup_executor(
      source=source,
      fetcher_parameters=context.fetcher_parameters,
      enable_cache=enable_cache,
      cache_ttl_seconds=cache_ttl_seconds,
      simulate=simulate,
      writers=context.writer,
      writer_parameters=context.writer_parameters,
    )
    if parallel_queries and len(batch) > 1:
      garf_logger.info('Running queries in parallel')
      query_executor.execute_batch(batch, context, parallel_threshold)
    else:
      if len(batch) > 1:
        garf_logger.info('Running queries sequentially')
      for title, text in batch.items():
        query_executor.execute(query=text, title=title, context=context)


@workflow_app.command(
  context_settings={'allow_extra_args': True, 'ignore_unknown_options': True},
)
@tracer.start_as_current_span('garf.cli.workflow.run')
def run(
  ctx: typer.Context,
  file: Annotated[
    str,
    typer.Option('--workflow', '-f', help='Workflow YAML file'),
  ],
  config: Annotated[
    Optional[str],
    typer.Option('--config', '-c', help='Yaml file with parameters'),
  ] = None,
  include: Annotated[
    Optional[str],
    typer.Option('--include', '-i', help='Steps of workflow to execute'),
  ] = None,
  exclude: Annotated[
    Optional[str],
    typer.Option('--exclude', '-e', help='Steps of workflow to skip'),
  ] = None,
  loglevel: LogLevel = 'INFO',
  logger: Logger = 'rich',
  log_name: LogName = 'garf',
  enable_cache: EnableCache = False,
  cache_ttl_seconds: CacheTTL = 3600,
  simulate: Simulate = False,
):
  """Runs workflow from a file."""
  span = trace.get_current_span()
  command_args = ' '.join(sys.argv[1:])
  span.set_attribute('cli.command', f'grf {command_args}')
  garf_logger = utils.init_logging(
    loglevel=loglevel.upper(), logger_type=logger, name=log_name
  )
  garf_logger.addHandler(initialize_logger())
  context = utils.ParamsParser().parse_all(ctx.args)
  _init_runner(file, context, config).run(
    enable_cache=enable_cache,
    cache_ttl_seconds=cache_ttl_seconds,
    selected_aliases=include,
    skipped_aliases=exclude,
    simulate=simulate,
  )


@workflow_app.command(
  context_settings={'allow_extra_args': True, 'ignore_unknown_options': True},
)
def compile(
  ctx: typer.Context,
  file: Annotated[
    str,
    typer.Option('--workflow', '-f', help='Workflow YAML file'),
  ],
  output_file: Annotated[
    Optional[str],
    typer.Option('--output-workflow', '-o', help='Output workflow YAML file'),
  ] = None,
  config: Annotated[
    Optional[str],
    typer.Option('--config', '-c', help='Yaml file with parameters'),
  ] = None,
):
  """Compiles workflow."""
  if not output_file:
    output_file = pathlib.Path(file).stem / '_compiled.yaml'
  context = utils.ParamsParser().parse_all(ctx.args)
  _init_runner(file, context, config).compile(output_file)


@workflow_app.command(
  context_settings={'allow_extra_args': True, 'ignore_unknown_options': True},
)
def deploy(
  ctx: typer.Context,
  file: Annotated[
    str,
    typer.Option('--workflow', '-f', help='Workflow YAML file'),
  ],
  output_file: Annotated[
    Optional[str],
    typer.Option('--output-workflow', '-o', help='Output workflow YAML file'),
  ] = None,
  config: Annotated[
    Optional[str],
    typer.Option('--config', '-c', help='Yaml file with parameters'),
  ] = None,
  embed_queries: Annotated[
    bool,
    typer.Option(
      help='Whether embed query texts into the output',
    ),
  ] = True,
):
  """Prepares deployment for Google Cloud Workflows."""
  if not output_file:
    output_file = pathlib.Path(file).stem / '_gcp.yaml'
  context = utils.ParamsParser().parse_all(ctx.args)
  _init_runner(file, context, config).deploy(
    path=output_file, embed_queries=embed_queries
  )


@typer_app.command()
def fetchers() -> set[str]:
  """Displays all available fetchers."""
  table = Table('Fetcher')
  for fetcher in setup.find_executors():
    table.add_row(fetcher)
  console.print(table)


@typer_app.command()
def version() -> str:
  """Shows version."""
  typer.echo(garf.executors.__version__)
  raise typer.Exit()


@typer_app.callback(
  invoke_without_command=True,
  context_settings={'allow_extra_args': True, 'ignore_unknown_options': True},
)
def main(
  ctx: typer.Context,
):
  ctx.obj = {}


if __name__ == '__main__':
  typer_app()
