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
import sys
from concurrent import futures

import garf_executors
from garf_executors import exceptions
from garf_executors.entrypoints import utils
from garf_io import reader


def main():
  parser = argparse.ArgumentParser()
  parser.add_argument('query', nargs='*')
  parser.add_argument('-c', '--config', dest='garf_config', default=None)
  parser.add_argument('--source', dest='source', default=None)
  parser.add_argument('--output', dest='output', default='console')
  parser.add_argument('--input', dest='input', default='file')
  parser.add_argument('--log', '--loglevel', dest='loglevel', default='info')
  parser.add_argument('--logger', dest='logger', default='local')
  parser.add_argument(
    '--parallel-queries', dest='parallel_queries', action='store_true'
  )
  parser.add_argument(
    '--no-parallel-queries', dest='parallel_queries', action='store_false'
  )
  parser.add_argument('--dry-run', dest='dry_run', action='store_true')
  parser.add_argument('-v', '--version', dest='version', action='store_true')
  parser.add_argument(
    '--parallel-threshold', dest='parallel_threshold', default=None, type=int
  )
  parser.set_defaults(parallel_queries=True)
  parser.set_defaults(dry_run=False)
  args, kwargs = parser.parse_known_args()

  if args.version:
    print(garf_executors.__version__)
    sys.exit()
  if not (source := args.source):
    raise exceptions.GarfExecutorError(
      f'Select one of available sources: {list(garf_executors.FETCHERS.keys())}'
    )
  if not (concrete_api_fetcher := garf_executors.FETCHERS.get(source)):
    raise exceptions.GarfExecutorError(f'Source {source} is not available.')

  logger = utils.init_logging(
    loglevel=args.loglevel.upper(), logger_type=args.logger
  )
  if not args.query:
    logger.error('Please provide one or more queries to run')
    raise exceptions.GarfExecutorError(
      'Please provide one or more queries to run'
    )
  config = utils.ConfigBuilder('garf').build(vars(args), kwargs)
  logger.debug('config: %s', config)

  if config.params:
    config = utils.initialize_runtime_parameters(config)
  logger.debug('initialized config: %s', config)

  extra_parameters = utils.ParamsParser(['source']).parse(kwargs)
  source_parameters = extra_parameters.get('source', {})
  reader_client = reader.create_reader(args.input)

  context = garf_executors.api_executor.ApiExecutionContext(
    query_parameters=config.params,
    writer=args.output,
    writer_parameters=config.writer_params,
    fetcher_parameters=source_parameters,
  )
  query_executor = garf_executors.api_executor.ApiQueryExecutor(
    concrete_api_fetcher(**source_parameters)
  )
  if args.parallel_queries:
    logger.info('Running queries in parallel')
    with futures.ThreadPoolExecutor(args.parallel_threshold) as executor:
      future_to_query = {
        executor.submit(
          query_executor.execute,
          reader_client.read(query),
          query,
          context,
        ): query
        for query in args.query
      }
      for future in futures.as_completed(future_to_query):
        future.result()
  else:
    logger.info('Running queries sequentially')
    for query in args.query:
      query_executor.execute(reader_client.read(query), query, context)


if __name__ == '__main__':
  main()
