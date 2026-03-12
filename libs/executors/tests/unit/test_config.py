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

import yaml
from garf.executors.config import Config


class TestConfig:
  def test_from_file_returns_correct_context_from_data(self, tmp_path):
    tmp_config = tmp_path / 'config.yaml'
    data = {
      'sources': {
        'api': {
          'query_parameters': {
            'macro': {
              'start_date': '2025-01-01',
            },
            'template': {
              'cohorts': 1,
            },
          },
          'fetcher_parameters': {
            'id': [1, 2, 3],
          },
          'writer': 'csv',
          'writer_parameters': {
            'destination_folder': '/tmp',
          },
        }
      }
    }
    with open(tmp_config, 'w', encoding='utf-8') as f:
      yaml.dump(data, f, encoding='utf-8')
    config = Config.from_file(tmp_config)
    expected_config = Config(**data)
    assert config == expected_config

  def test_save_returns_correct_data(self, tmp_path):
    tmp_config = tmp_path / 'config.yaml'
    data = {
      'sources': {
        'api': {
          'query_parameters': {
            'macro': {
              'start_date': '2025-01-01',
            },
            'template': {
              'cohorts': 1,
            },
          },
          'fetcher_parameters': {
            'id': [1, 2, 3],
          },
          'writer': 'csv',
          'writer_parameters': {
            'destination_folder': '/tmp',
          },
        }
      }
    }
    config = Config(**data)
    config.save(tmp_config)
    with open(tmp_config, 'r', encoding='utf-8') as f:
      config_data = yaml.safe_load(f)
    assert config_data == data

  def test_expand(self):
    data = {
      'global_parameters': {
        'query_parameters': {
          'macro': {
            'start_date': '2025-01-01',
            'end_date': '2025-12-31',
          },
        },
        'writer_parameters': {
          'destination_folder': '/tmp/data',
        },
      },
      'sources': {
        'api': {
          'query_parameters': {
            'macro': {
              'start_date': '2025-12-01',
            },
            'template': {
              'cohorts': 1,
            },
          },
          'writer': 'csv',
          'writer_parameters': {
            'destination_folder': '/tmp',
          },
        },
        'api2': {
          'writer': 'csv',
        },
      },
    }
    config = Config(**data).expand()
    expected_query_parameters = {
      'macro': {
        'start_date': '2025-12-01',
        'end_date': '2025-12-31',
      },
      'template': {
        'cohorts': 1,
      },
    }
    assert (
      config.sources.get('api').query_parameters.model_dump()
      == expected_query_parameters
    )
    assert config.sources.get('api').writer_parameters == {
      'destination_folder': '/tmp',
    }
    assert config.sources.get('api2').query_parameters.model_dump().get(
      'macro'
    ) == data.get('global_parameters').get('query_parameters').get('macro')
    assert config.sources.get('api2').writer_parameters == {
      'destination_folder': '/tmp/data',
    }
