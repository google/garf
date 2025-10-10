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
"""Module for defining `garf` CLI utility.

`garf` allows to execute queries and store results in local/remote
storage.
"""

from __future__ import annotations

from typing import Optional

import typer
from garf_io import reader
from typing_extensions import Annotated

import garf_executors
from garf_executors import exceptions
from garf_executors.config import Config
from garf_executors.entrypoints import utils

typer_app = typer.Typer()


def _version_callback(show_version: bool) -> None:
  if show_version:
    print(f'Garf version: {garf_executors.__version__}')
    raise typer.Exit()


@typer_app.command(
  context_settings={'allow_extra_args': True, 'ignore_unknown_options': True}
)
def main(
  source: Annotated[str, typer.Option(help='API alias')],
  queries: Annotated[
    list[str], typer.Argument(help='One or several query files')
  ],
  config: Annotated[
    Optional[str],
    typer.Option('--config', '-c', help='Yaml file with parameters for garf'),
  ] = None,
  input: Annotated[
    str,
    typer.Option(help='Where to get queries from'),
  ] = 'file',
  output: Annotated[
    str,
    typer.Option(help='Where to write data'),
  ] = 'console',
  parallel_queries: Annotated[
    bool, typer.Option(help='Whether to run queries in parallel')
  ] = True,
  version: Annotated[
    bool,
    typer.Option(
      help='Display version of garf',
      callback=_version_callback,
      is_eager=True,
      expose_value=False,
    ),
  ] = False,
  loglevel: Annotated[
    str,
    typer.Option(help='Level of logging'),
  ] = 'INFO',
  logger: Annotated[
    str,
    typer.Option(help='Type of logging'),
  ] = 'rich',
) -> None:
  garf_logger = utils.init_logging(
    loglevel=loglevel.upper(), logger_type=logger
  )
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
  reader_client = reader.create_reader(input)
  if config:
    garf_logger.info('Running queries with config: %s', config)
    execution_config = Config.from_file(config)
    if not (context := execution_config.sources.get(source)):
      raise exceptions.GarfExecutorError(
        f'No execution context found for source {source} in {config}'
      )
    query_executor = garf_executors.setup_executor(
      source, context.fetcher_parameters
    )
    batch = {query: reader_client.read(query) for query in found_queries}
    query_executor.execute_batch(batch, context, parallel_queries)
  else:
    extra_parameters = utils.ParamsParser(
      ['source', output, 'macro', 'template']
    ).parse(parameters)
    source_parameters = extra_parameters.get('source', {})

    context = garf_executors.api_executor.ApiExecutionContext(
      query_parameters={
        'macro': extra_parameters.get('macro'),
        'template': extra_parameters.get('template'),
      },
      writer=output,
      writer_parameters=extra_parameters.get(output),
      fetcher_parameters=source_parameters,
    )
    query_executor = garf_executors.setup_executor(
      source, context.fetcher_parameters
    )
    if parallel_queries:
      garf_logger.info('Running queries in parallel')
      batch = {query: reader_client.read(query) for query in found_queries}
      query_executor.execute_batch(batch, context, parallel_queries)
    else:
      garf_logger.info('Running queries sequentially')
      for query in found_queries:
        query_executor.execute(reader_client.read(query), query, context)


if __name__ == '__main__':
  typer_app()
