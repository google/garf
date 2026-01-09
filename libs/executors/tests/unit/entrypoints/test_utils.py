# Copyright 2024 Google LLC
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
from __future__ import annotations

import pytest
from garf.executors.entrypoints import utils


class TestParamsParser:
  @pytest.fixture
  def param_parser(self):
    return utils.ParamsParser(['macro', 'template'])

  def test_if_incorrect_param_is_provided(self, param_parser):
    with pytest.raises(utils.GarfParamsException):
      param_parser.parse(
        ['--macros.start_date=2022-01-01', '--fake_param.end_date=2022-12-31']
      )

  def test_parse_raises_error_on_missing_identifier(self, param_parser):
    with pytest.raises(utils.GarfParamsException, match='correct formats'):
      param_parser.parse(['--macro.'])

  def test_parse_raises_error_on_incorrect_format(self, param_parser):
    with pytest.raises(utils.GarfParamsException, match='correct formats'):
      param_parser.parse(['--macro.key.sub_key=value'])

  def test_identify_param_pair_existing(self, param_parser):
    param_pair = param_parser._identify_param_pair(
      'macro', ['--macro.start_date', '2022-01-01']
    )
    assert param_pair == {'start_date': '2022-01-01'}

  def test_identify_param_pair_empty(self, param_parser):
    param_pair = param_parser._identify_param_pair(
      'macro', ['--missing_param.start_date', '2022-01-01']
    )
    assert param_pair is None

  def test_identify_param_pair_raises_error(self, param_parser):
    with pytest.raises(utils.GarfParamsException):
      param_parser._identify_param_pair(
        'macro', ['--macro.start_date', ':YYYYMMDD', 'extra_element']
      )

  def test_parse_params(self, param_parser):
    parsed_params = param_parser._parse_params(
      'macro', ['--macro.start_date=2022-01-01', '--macro.end_date=2022-12-31']
    )
    assert parsed_params == {
      'start_date': '2022-01-01',
      'end_date': '2022-12-31',
    }

  def test_parse(self, param_parser):
    parsed_params = param_parser.parse(
      [
        '--macro.start_date=2022-01-01',
        '--macro.end_date=2022-12-31',
        '--macro.active',
      ]
    )
    assert parsed_params == {
      'macro': {
        'start_date': '2022-01-01',
        'end_date': '2022-12-31',
        'active': True,
      },
      'template': {},
    }


@pytest.mark.parametrize(
  'logger_type',
  ['local', 'rich', utils.LoggerEnum.local, utils.LoggerEnum.rich],
)
def test_init_logging(logger_type):
  assert utils.init_logging(logger_type=logger_type)
