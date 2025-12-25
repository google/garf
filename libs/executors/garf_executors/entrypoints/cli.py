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

import argparse
import logging
import sys

from garf_io import reader

import garf_executors
from garf_executors import config, exceptions
from garf_executors.entrypoints import utils
from garf_executors.entrypoints.tracer import initialize_tracer
from garf_executors.telemetry import tracer

initialize_tracer()


@tracer.start_as_current_span('garf.entrypoints.cli')
def main():
  parser = argparse.ArgumentParser()
  parser.add_argument('query', nargs='*')
  parser.add_argument('-c', '--config', dest='config', default=None)
  parser.add_argument('--source', dest='source', default=None)
  parser.add_argument('--output', dest='output', default='console')
  parser.add_argument('--input', dest='input', default='file')
  parser.add_argument('--log', '--loglevel', dest='loglevel', default='info')
  parser.add_argument('--logger', dest='logger', default='local')
  parser.add_argument('--log-name', dest='log_name', default='garf')
  parser.add_argument(
    '--parallel-queries', dest='parallel_queries', action='store_true'
  )
  parser.add_argument(
    '--no-parallel-queries', dest='parallel_queries', action='store_false'
  )
  parser.add_argument('--dry-run', dest='dry_run', action='store_true')
  parser.add_argument('-v', '--version', dest='version', action='store_true')
  parser.add_argument(
    '--parallel-threshold', dest='parallel_threshold', default=10, type=int
  )
  parser.add_argument(
    '--enable-cache', dest='enable_cache', action='store_true'
  )
  parser.add_argument(
    '--cache-ttl-seconds',
    dest='cache_ttl_seconds',
    default=3600,
    type=int,
  )
  parser.set_defaults(parallel_queries=True)
  parser.set_defaults(enable_cache=False)
  parser.set_defaults(dry_run=False)
  args, kwargs = parser.parse_known_args()

  if args.version:
    print(garf_executors.__version__)
    sys.exit()
  logger = utils.init_logging(
    loglevel=args.loglevel.upper(), logger_type=args.logger, name=args.log_name
  )
  if not args.query:
    logger.error('Please provide one or more queries to run')
    raise exceptions.GarfExecutorError(
      'Please provide one or more queries to run'
    )
  reader_client = reader.create_reader(args.input)
  if config_file := args.config:
    execution_config = config.Config.from_file(config_file)
    if not (context := execution_config.sources.get(args.source)):
      raise exceptions.GarfExecutorError(
        f'No execution context found for source {args.source} in {config_file}'
      )
    query_executor = garf_executors.setup_executor(
      source=args.source,
      fetcher_parameters=context.fetcher_parameters,
      enable_cache=args.enable_cache,
      cache_ttl_seconds=args.cache_ttl_seconds,
    )
    batch = {query: reader_client.read(query) for query in args.query}
    query_executor.execute_batch(batch, context, args.parallel_threshold)
  else:
    param_types = ['source', 'macro', 'template']
    outputs = args.output.split(',')
    extra_parameters = utils.ParamsParser([*param_types, *outputs]).parse(
      kwargs
    )
    source_parameters = extra_parameters.get('source', {})
    writer_parameters = {}
    for output in outputs:
      writer_parameters.update(extra_parameters.get(output))

    context = garf_executors.api_executor.ApiExecutionContext(
      query_parameters={
        'macro': extra_parameters.get('macro'),
        'template': extra_parameters.get('template'),
      },
      writer=outputs,
      writer_parameters=writer_parameters,
      fetcher_parameters=source_parameters,
    )
    query_executor = garf_executors.setup_executor(
      source=args.source,
      fetcher_parameters=context.fetcher_parameters,
      enable_cache=args.enable_cache,
      cache_ttl_seconds=args.cache_ttl_seconds,
    )
    if args.parallel_queries and len(args.query) > 1:
      logger.info('Running queries in parallel')
      batch = {query: reader_client.read(query) for query in args.query}
      query_executor.execute_batch(batch, context, args.parallel_threshold)
    else:
      if len(args.query) > 1:
        logger.info('Running queries sequentially')
      for query in args.query:
        query_executor.execute(
          query=reader_client.read(query), title=query, context=context
        )
  logging.shutdown()


if __name__ == '__main__':
  main()
