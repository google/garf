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

import asyncio
import json
import pathlib

import garf.executors
from garf.executors.entrypoints.mcp_server import mcp

_SCRIPT_PATH = pathlib.Path(__file__).parent


class TestMcpServer:
  query = (
    'SELECT dimension.string AS resource, '
    'dimensions.string AS name, metrics.int AS clicks '
    'FROM fake'
  )

  def test_list_tools_excludes_tasks(self):
    tools = asyncio.run(mcp.list_tools())
    tool_names = {tool.name for tool in tools}
    assert tool_names == {'execute', 'execute_batch', 'execute_workflow'}

  def test_list_and_read_resources(self):
    resources = asyncio.run(mcp.list_resources())
    resource_names = {resource.name for resource in resources}
    assert resource_names == {'version', 'info', 'fetchers', 'executors'}

    version_res = asyncio.run(mcp.read_resource('resource://version'))
    assert (
      json.loads(version_res.contents[0].content)
      == garf.executors.version.__version__
    )

    info_res = asyncio.run(mcp.read_resource('resource://info'))
    info_data = json.loads(info_res.contents[0].content)
    assert info_data == {
      'executors': garf.executors.version.__version__,
      'core': garf.executors.version.core_version,
      'io': garf.executors.version.io_version,
    }

    fetchers_res = asyncio.run(mcp.read_resource('resource://fetchers'))
    fetchers_data = json.loads(fetchers_res.contents[0].content)
    assert 'fake' in fetchers_data

    executors_res = asyncio.run(mcp.read_resource('resource://executors'))
    executors_data = json.loads(executors_res.contents[0].content)
    assert 'api' in executors_data

  def test_execute_fake_source_from_query_text(self, tmp_path):
    request = {
      'source': 'fake',
      'query': self.query,
      'title': 'test',
      'context': {
        'fetcher_parameters': {
          'n_rows': 1,
        },
        'writer': 'csv',
        'writer_parameters': {'destination_folder': str(tmp_path)},
      },
    }
    response = asyncio.run(mcp.call_tool('execute', request))
    tmp_path_output = f'{tmp_path}/test.csv'
    query_output_path = f'[CSV] - at {tmp_path_output}'
    expected_output = {
      'results': [query_output_path],
      'full_results': {'test': [query_output_path]},
    }
    assert response.structured_content == expected_output

  def test_execute_fake_source_from_query_path(self, tmp_path):
    query_path = tmp_path / 'query.sql'
    with pathlib.Path.open(query_path, 'w', encoding='utf-8') as f:
      f.write(self.query)
    request = {
      'source': 'fake',
      'query_path': str(query_path),
      'context': {
        'fetcher_parameters': {
          'n_rows': 1,
        },
        'writer': 'csv',
        'writer_parameters': {'destination_folder': str(tmp_path)},
      },
    }
    response = asyncio.run(mcp.call_tool('execute', request))
    tmp_path_output = f'{tmp_path}/query.csv'
    query_output_path = f'[CSV] - at {tmp_path_output}'
    expected_output = {
      'results': [query_output_path],
      'full_results': {str(query_path): [query_output_path]},
    }
    assert response.structured_content == expected_output

  def test_execute_batch_returns_report_results_with_no_writer(self):
    request = {
      'source': 'fake',
      'batch': {
        'query1': self.query,
      },
      'context': {
        'fetcher_parameters': {
          'n_rows': 1,
        },
      },
    }
    response = asyncio.run(mcp.call_tool('execute_batch', request))
    payload = response.structured_content
    assert payload.get('results') == ['query1']
    expected_report_columns = ['resource', 'name', 'clicks']
    for result in payload.get('full_results').values():
      assert list(result[0].keys()) == expected_report_columns

  def test_execute_workflow_from_file_no_writer(self):
    workflow_path = _SCRIPT_PATH / 'test_workflow_no_writer.yaml'
    request = {
      'workflow_path': str(workflow_path),
    }
    response = asyncio.run(mcp.call_tool('execute_workflow', request))
    payload = response.structured_content
    step_value = payload.get('1-fake-test')
    assert step_value.get('results') == ['test_query']
    expected_report_columns = ['name', 'clicks']
    for result in step_value.get('full_results').values():
      assert list(result[0].keys()) == expected_report_columns
