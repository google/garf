# Copyright 2022 Google LLC
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
"""Module for various helpers for executing Garf as CLI tool."""

from __future__ import annotations

import enum
import logging
import sys
from collections.abc import Sequence
from typing import Any

from rich import logging as rich_logging


class ParamsParser:
  def __init__(self, identifiers: Sequence[str]) -> None:
    self.identifiers = identifiers

  def parse(self, params: Sequence) -> dict[str, dict | None]:
    return {
      identifier: self._parse_params(identifier, params)
      for identifier in self.identifiers
    }

  def _parse_params(self, identifier: str, params: Sequence[Any]) -> dict:
    parsed_params = {}
    if params:
      raw_params = [param.split('=', maxsplit=1) for param in params]
      for param in raw_params:
        param_pair = self._identify_param_pair(identifier, param)
        if param_pair:
          parsed_params.update(param_pair)
    return parsed_params

  def _identify_param_pair(
    self, identifier: str, param: Sequence[str]
  ) -> dict[str, Any] | None:
    key = param[0]
    if not identifier or identifier not in key:
      return None
    provided_identifier, *keys = key.split('.')
    if not keys:
      return None
    if len(keys) > 1:
      raise GarfParamsException(
        f'{key} is invalid format,'
        f'`--{identifier}.key=value` or `--{identifier}.key` '
        'are the correct formats'
      )
    provided_identifier = provided_identifier.replace('--', '')
    if provided_identifier not in self.identifiers:
      supported_arguments = ', '.join(self.identifiers)
      raise GarfParamsException(
        f'CLI argument {provided_identifier} is not supported'
        f', supported arguments {supported_arguments}'
      )
    if provided_identifier != identifier:
      return None
    key = keys[0].replace('-', '_')
    if not key:
      raise GarfParamsException(
        f'{identifier} {key} is invalid,'
        f'`--{identifier}.key=value` or `--{identifier}.key` '
        'are the correct formats'
      )
    if len(param) == 2:
      return {key: param[1]}
    if len(param) == 1:
      return {key: True}
    raise GarfParamsException(
      f'{identifier} {key} is invalid,'
      f'`--{identifier}.key=value` or `--{identifier}.key` '
      'are the correct formats'
    )


class GarfParamsException(Exception):
  """Defines exception for incorrect parameters."""


class LoggerEnum(str, enum.Enum):
  local = 'local'
  rich = 'rich'
  gcloud = 'gcloud'


def init_logging(
  loglevel: str = 'INFO',
  logger_type: str | LoggerEnum = 'local',
  name: str = __name__,
) -> logging.Logger:
  loglevel = getattr(logging, loglevel)
  if logger_type == 'rich':
    logging.basicConfig(
      format='%(message)s',
      level=loglevel,
      datefmt='%Y-%m-%d %H:%M:%S',
      handlers=[
        rich_logging.RichHandler(rich_tracebacks=True),
      ],
    )
  elif logger_type == 'gcloud':
    try:
      import google.cloud.logging as glogging
    except ImportError as e:
      raise ImportError(
        'Please install garf-executors with Cloud logging support - '
        '`pip install garf-executors[bq]`'
      ) from e

    client = glogging.Client()
    handler = glogging.handlers.CloudLoggingHandler(client, name=name)
    handler.close()
    glogging.handlers.setup_logging(handler, log_level=loglevel)
    logging.basicConfig(
      level=loglevel,
      handlers=[handler],
    )
  else:
    logging.basicConfig(
      format='[%(asctime)s][%(name)s][%(levelname)s] %(message)s',
      stream=sys.stdout,
      level=loglevel,
      datefmt='%Y-%m-%d %H:%M:%S',
    )
  logging.getLogger('smart_open.smart_open_lib').setLevel(logging.WARNING)
  logging.getLogger('urllib3.connectionpool').setLevel(logging.WARNING)
  return logging.getLogger(name)
