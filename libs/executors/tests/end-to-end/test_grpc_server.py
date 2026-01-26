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
from garf.executors import garf_pb2 as pb
from garf.executors import garf_pb2_grpc
from garf.executors.entrypoints import grpc_server
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
