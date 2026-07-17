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
import pathlib

import pytest
from garf.executors import fetchers, garf_pb2_grpc, setup, version
from garf.executors import garf_pb2 as pb
from garf.executors.entrypoints import grpc_server
from google.protobuf import empty_pb2
from google.protobuf.json_format import MessageToDict

_SCRIPT_PATH = pathlib.Path(__file__).parent
_QUERY = """
  SELECT
    resource,
    dimensions.name AS name,
    metrics.clicks AS clicks
  FROM resource
"""
expected_output = [
  {
    'resource': 'Campaign A',
    'name': 'Ad Group 1',
    'clicks': 1500,
  },
  {
    'resource': 'Campaign B',
    'name': 'Ad Group 2',
    'clicks': 2300,
  },
  {
    'resource': 'Campaign C',
    'name': 'Ad Group 3',
    'clicks': 800,
  },
  {
    'resource': 'Campaign A',
    'name': 'Ad Group 4',
    'clicks': 3200,
  },
]


@pytest.fixture(scope='module')
def grpc_add_to_server():
  return garf_pb2_grpc.add_GarfServiceServicer_to_server


@pytest.fixture(scope='module')
def grpc_servicer():
  return grpc_server.GarfService()


@pytest.fixture(scope='module')
def grpc_stub_cls(grpc_channel):
  return garf_pb2_grpc.GarfServiceStub


def test_execute(grpc_stub):
  fake_data = _SCRIPT_PATH / 'test.json'
  request = pb.ExecuteRequest(
    source='fake',
    title='example',
    query=_QUERY,
    context=pb.ExecutionContext(
      fetcher_parameters={
        'data_location': str(fake_data),
      },
      writer='csv',
    ),
  )
  result = grpc_stub.Execute(request)
  assert 'CSV' in result.results[0]


def test_execute_batch(grpc_stub):
  request = pb.ExecuteBatchRequest(
    source='fake',
    batch=[
      pb.QueryDefinition(
        title='example',
        text='SELECT metric.int FROM fake',
      )
    ],
    context=pb.ExecutionContext(
      fetcher_parameters={
        'n_rows': 1,
      },
      writer='csv',
    ),
  )
  result = grpc_stub.ExecuteBatch(request)
  assert 'example' in result.results[0]


def test_fetch(grpc_stub):
  fake_data = _SCRIPT_PATH / 'test.json'
  request = pb.FetchRequest(
    source='fake',
    title='example',
    query=_QUERY,
    context=pb.FetchContext(
      fetcher_parameters={
        'data_location': str(fake_data),
      }
    ),
  )
  result = grpc_stub.Fetch(request)
  data = [MessageToDict(r) for r in result.rows]
  assert result.columns == ['resource', 'name', 'clicks']
  assert data == expected_output


def test_execute_workflow(grpc_stub):
  request = pb.ExecuteWorkflowRequest(
    workflow=pb.Workflow(
      name='test',
      steps=[
        pb.WorkflowStep(
          fetcher='fake',
          alias='test',
          queries=[
            pb.QueryDefinition(
              title='example',
              text='SELECT metric.int FROM fake',
            )
          ],
          fetcher_parameters={
            'n_rows': 1,
          },
          writer='csv',
        ),
      ],
    ),
  )
  result = grpc_stub.ExecuteWorkflow(request)
  assert '1-fake-test' in result.results[0]


def test_garf_version(grpc_stub):
  result = grpc_stub.GetVersion(empty_pb2.Empty())
  assert result.version == version.__version__


def test_garf_info(grpc_stub):
  result = grpc_stub.GetInfo(empty_pb2.Empty())
  expected_response = pb.GarfInfo(
    executors_version=version.__version__,
    core_version=version.core_version,
    io_version=version.io_version,
  )
  assert result == expected_response


def test_list_fetchers(grpc_stub):
  result = grpc_stub.ListFetchers(empty_pb2.Empty())
  expected_response = pb.ListFetchersResponse(
    results=[
      pb.FetcherInfo(name=name, version=fetcher.version)
      for name, fetcher in fetchers.get_all_report_fetchers().items()
    ]
  )
  assert result == expected_response


def test_list_executors(grpc_stub):
  result = grpc_stub.ListExecutors(empty_pb2.Empty())
  expected_response = pb.ListExecutorsResponse(
    results=setup.available_executors()
  )
  assert result == expected_response
