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

import dataclasses
import datetime
import logging
import os
import sys
from collections.abc import MutableSequence, Sequence
from typing import Any, TypedDict

import smart_open
import yaml
from dateutil import relativedelta
from rich import logging as rich_logging

from garf_core import query_editor


class GarfQueryParameters(TypedDict):
  """Annotation for dictionary of query specific parameters passed via CLI.

  Attributes:
      macros: Mapping for elements that will be replaced in the queries.
      template: Mapping for elements that will rendered via Jinja templates.
  """

  macros: dict[str, str]
  template: dict[str, str]


@dataclasses.dataclass
class BaseConfig:
  """Base config to inherit other configs from."""

  def __add__(self, other: BaseConfig) -> BaseConfig:
    """Creates new config of the same type from two configs.

    Parameters from added config overwrite already present parameters.

    Args:
        other: Config that could be merged with the original one.

    Returns:
        New config with values from both configs.
    """
    right_dict = _remove_empty_values(self.__dict__)
    left_dict = _remove_empty_values(other.__dict__)
    new_dict = {**right_dict, **left_dict}
    return self.__class__(**new_dict)

  @classmethod
  def from_dict(
    cls, config_parameters: dict[str, str | GarfQueryParameters]
  ) -> BaseConfig:
    """Builds config from provided parameters ignoring empty ones."""
    return cls(**_remove_empty_values(config_parameters))


@dataclasses.dataclass
class GarfConfig(BaseConfig):
  """Stores values to run garf from command line.

  Attributes:
      account:
          Account(s) to get data from.
      output:
          Specifies where to store fetched data (console, csv, BQ.)
      api_version:
          Google Ads API version.
      params:
          Any parameters passed to Garf query for substitution.
      writer_params:
          Any parameters that can be passed to writer for data saving.
      customer_ids_query:
          Query text to limit accounts fetched from Ads API.
      customer_ids_query_file:
          Path to query to limit accounts fetched from Ads API.
  """

  account: str | list[str] | None = None
  output: str = 'console'
  params: GarfQueryParameters = dataclasses.field(default_factory=dict)
  writer_params: dict[str, str | int] = dataclasses.field(default_factory=dict)
  customer_ids_query: str | None = None
  customer_ids_query_file: str | None = None

  def __post_init__(self) -> None:
    """Ensures that values passed during __init__ correctly formatted."""
    if isinstance(self.account, MutableSequence):
      self.account = [
        str(account).replace('-', '').strip() for account in self.account
      ]
    else:
      self.account = (
        str(self.account).replace('-', '').strip() if self.account else None
      )
    self.writer_params = {
      key.replace('-', '_'): value for key, value in self.writer_params.items()
    }


class GarfConfigException(Exception):
  """Exception for invalid GarfConfig."""


@dataclasses.dataclass
class GarfBqConfig(BaseConfig):
  """Stores values to run garf-bq from command line.

  Attributes:
      project:
         Google Cloud project name.
      dataset_location:
          Location of BigQuery dataset.
      params:
          Any parameters passed to BigQuery query for substitution.
  """

  project: str | None = None
  dataset_location: str | None = None
  params: GarfQueryParameters = dataclasses.field(default_factory=dict)


@dataclasses.dataclass
class GarfSqlConfig(BaseConfig):
  """Stores values to run garf-sql from command line.

  Attributes:
      connection_string:
         Connection string to SqlAlchemy database engine.
      params:
          Any parameters passed to SQL query for substitution.
  """

  connection_string: str | None = None
  params: GarfQueryParameters = dataclasses.field(default_factory=dict)


class ConfigBuilder:
  """Builds config of provided type.

  Config can be created from file, build from arguments or both.

  Attributes:
      config: Concrete config class that needs to be built.
  """

  _config_mapping: dict[str, BaseConfig] = {
    'garf': GarfConfig,
    'garf-bq': GarfBqConfig,
    'garf-sql': GarfSqlConfig,
  }

  def __init__(self, config_type: str) -> None:
    """Sets concrete config type.

    Args:
        config_type: Type of config that should be built.

    Raises:
        GarfConfigException: When incorrect config_type is supplied.
    """
    if config_type not in self._config_mapping:
      raise GarfConfigException(f'Invalid config_type: {config_type}')
    self._config_type = config_type
    self.config = self._config_mapping.get(config_type)

  def build(
    self, parameters: dict[str, str], cli_named_args: Sequence[str]
  ) -> BaseConfig | None:
    """Builds config from file, build from arguments or both ways.

    When there are both config_file and CLI arguments the latter have more
    priority.

    Args:
        parameters: Parsed CLI arguments.
        cli_named_args: Unparsed CLI args in a form `--key.subkey=value`.

    Returns:
        Concrete config with injected values.
    """
    if not (garf_config_path := parameters.get('garf_config')):
      return self._build_config(parameters, cli_named_args)
    config_file = self._load_config(garf_config_path)
    config_cli = self._build_config(
      parameters, cli_named_args, init_defaults=False
    )
    if config_file and config_cli:
      config_file = config_file + config_cli
    return config_file

  def _build_config(
    self,
    parameters: dict[str, str],
    cli_named_args: Sequence[str],
    init_defaults: bool = True,
  ) -> BaseConfig | None:
    """Builds config from named and unnamed CLI parameters.

    Args:
        parameters: Parsed CLI arguments.
        cli_named_args: Unparsed CLI args in a form `--key.subkey=value`.
        init_defaults: Whether to provided default config values if
            expected parameter is missing

    Returns:
        Concrete config with injected values.
    """
    output = parameters.get('output')
    config_parameters = {
      k: v for k, v in parameters.items() if k in self.config.__annotations__
    }
    cli_params = ParamsParser(['macro', 'template', output]).parse(
      cli_named_args
    )
    cli_params = _remove_empty_values(cli_params)
    if output and (writer_params := cli_params.get(output)):
      _ = cli_params.pop(output)
      config_parameters.update({'writer_params': writer_params})
    if cli_params:
      config_parameters.update({'params': cli_params})
    if not config_parameters:
      return None
    if init_defaults:
      return self.config.from_dict(config_parameters)
    return self.config(**config_parameters)

  def _load_config(self, garf_config_path: str) -> BaseConfig:
    """Loads config from provided path.

    Args:
        garf_config_path: Path to local or remote storage.

    Returns:
        Concreate config with values taken from config file.

    Raises:
        GarfConfigException:
            If config file missing `garf` section.
    """
    with smart_open.open(garf_config_path, encoding='utf-8') as f:
      config = yaml.safe_load(f)
    garf_section = config.get(self._config_type)
    if not garf_section:
      raise GarfConfigException(
        f'Invalid config, must have `{self._config_type}` section!'
      )
    config_parameters = {
      k: v for k, v in garf_section.items() if k in self.config.__annotations__
    }
    if params := garf_section.get('params', {}):
      config_parameters.update({'params': params})
    if writer_params := garf_section.get(garf_section.get('output', '')):
      config_parameters.update({'writer_params': writer_params})
    return self.config(**config_parameters)


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
    if len(keys) > 1:
      raise GarfParamsException(
        f'{key} is invalid format,'
        f'`--{identifier}.key=value` or `--{identifier}.key` '
        'are the correct formats'
      )
    provided_identifier = provided_identifier.replace('--', '')
    if provided_identifier not in self.identifiers:
      raise GarfParamsException(
        f'CLI argument {provided_identifier} is not supported'
        f', supported arguments {", ".join(self.identifiers)}'
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


def convert_date(date_string: str) -> str:
  """Converts specific dates parameters to actual dates.

  Returns:
      Date string in YYYY-MM-DD format.

  Raises:
      ValueError:
          If dynamic lookback value (:YYYYMMDD-N) is incorrect.
  """
  if isinstance(date_string, list) or date_string.find(':YYYY') == -1:
    return date_string
  current_date = datetime.date.today()
  date_object = date_string.split('-')
  base_date = date_object[0]
  if len(date_object) == 2:
    try:
      days_ago = int(date_object[1])
    except ValueError as e:
      raise ValueError(
        'Must provide numeric value for a number lookback period, '
        'i.e. :YYYYMMDD-1'
      ) from e
  else:
    days_ago = 0
  if base_date == ':YYYY':
    new_date = datetime.datetime(current_date.year, 1, 1)
    delta = relativedelta.relativedelta(years=days_ago)
  elif base_date == ':YYYYMM':
    new_date = datetime.datetime(current_date.year, current_date.month, 1)
    delta = relativedelta.relativedelta(months=days_ago)
  elif base_date == ':YYYYMMDD':
    new_date = current_date
    delta = relativedelta.relativedelta(days=days_ago)
  return (new_date - delta).strftime('%Y-%m-%d')


class ConfigSaver:
  def __init__(self, path: str) -> None:
    self.path = path

  def save(self, garf_config: BaseConfig):
    if os.path.exists(self.path):
      with smart_open.open(self.path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    else:
      config = {}
    config = self.prepare_config(config, garf_config)
    with smart_open.open(self.path, 'w', encoding='utf-8') as f:
      yaml.dump(
        config, f, default_flow_style=False, sort_keys=False, encoding='utf-8'
      )

  def prepare_config(self, config: dict, garf_config: BaseConfig) -> dict:
    garf = dataclasses.asdict(garf_config)
    if isinstance(garf_config, GarfConfig):
      garf[garf_config.output] = garf_config.writer_params
      if not isinstance(garf_config.account, MutableSequence):
        garf['account'] = garf_config.account.split(',')
      del garf['writer_params']
      garf = _remove_empty_values(garf)
      config.update({'garf': garf})
    if isinstance(garf_config, GarfBqConfig):
      garf = _remove_empty_values(garf)
      config.update({'garf-bq': garf})
    if isinstance(garf_config, GarfSqlConfig):
      garf = _remove_empty_values(garf)
      config.update({'garf-sql': garf})
    return config


def initialize_runtime_parameters(config: BaseConfig) -> BaseConfig:
  """Formats parameters and add common parameter in config.

  Initialization identifies whether there are `date` parameters and performs
  necessary date conversions.
  Set of parameters that need to be generally available are injected into
  every parameter section of the config.

  Args:
      config: Instantiated config.

  Returns:
      Config with formatted parameters.
  """
  common_params = query_editor.CommonParametersMixin().common_params
  for key, param in config.params.items():
    for key_param, value_param in param.items():
      config.params[key][key_param] = convert_date(value_param)
    for common_param_key, common_param_value in common_params.items():
      if common_param_key not in config.params[key]:
        config.params[key][common_param_key] = common_param_value
  return config


def _remove_empty_values(dict_object: dict[str, Any]) -> dict[str, Any]:
  """Remove all empty elements: strings, dictionaries from a dictionary."""
  if isinstance(dict_object, dict):
    return {
      key: value
      for key, value in (
        (key, _remove_empty_values(value)) for key, value in dict_object.items()
      )
      if value
    }
  if isinstance(dict_object, (int, str, MutableSequence)):
    return dict_object


def init_logging(
  loglevel: str = 'INFO', logger_type: str = 'local', name: str = __name__
) -> logging.Logger:
  if logger_type == 'rich':
    logging.basicConfig(
      format='%(message)s',
      level=loglevel,
      datefmt='%Y-%m-%d %H:%M:%S',
      handlers=[
        rich_logging.RichHandler(rich_tracebacks=True),
      ],
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
