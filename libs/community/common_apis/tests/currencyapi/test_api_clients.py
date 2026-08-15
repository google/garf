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

"""Tests for CurrencyApiClient."""

import pytest
import responses as responses_lib
from garf.community.common_apis.currencyapi.api_clients import (
  CurrencyApiClient,
  CurrencyApiClientError,
  _DEFAULT_ENDPOINT,
)
from garf.core.query_editor import BaseQueryElements


@pytest.fixture
def query():
  return BaseQueryElements(
    title=None,
    text='SELECT code, value FROM latest WHERE base_currency=EUR',
    resource_name='latest',
    fields=['code', 'value'],
    filters=['base_currency=EUR'],
    column_names=['code', 'rate'],
  )


@pytest.fixture
def client():
  return CurrencyApiClient(api_key='test-key')


@pytest.fixture
def currency_payload():
  return {
    'meta': {'last_updated_at': '2026-01-01T00:00:00Z'},
    'data': {
      'USD': {'code': 'USD', 'value': 108},
      'GBP': {'code': 'GBP', 'value': 85},
    },
  }


@pytest.mark.parametrize('bad_key', ['', None])
def test_raises_on_missing_api_key(bad_key):
  with pytest.raises(CurrencyApiClientError, match='key'):
    CurrencyApiClient(api_key=bad_key)


def test_api_key_not_stored_in_query_args():
  c = CurrencyApiClient(api_key='secret-key')
  assert 'secret-key' not in str(c.query_args)


@responses_lib.activate
def test_injects_api_key_as_header(client, query, currency_payload):
  responses_lib.add(responses_lib.GET, f'{_DEFAULT_ENDPOINT}/latest', json=currency_payload)
  client.get_response(query)
  assert responses_lib.calls[0].request.headers.get('apikey') == 'test-key'


@responses_lib.activate
def test_api_key_not_in_url(client, query, currency_payload):
  responses_lib.add(responses_lib.GET, f'{_DEFAULT_ENDPOINT}/latest', json=currency_payload)
  client.get_response(query)
  assert 'test-key' not in responses_lib.calls[0].request.url


@responses_lib.activate
def test_filters_passed_as_query_params(client, query, currency_payload):
  responses_lib.add(responses_lib.GET, f'{_DEFAULT_ENDPOINT}/latest', json=currency_payload)
  client.get_response(query)
  assert 'base_currency=EUR' in responses_lib.calls[0].request.url


@responses_lib.activate
def test_api_key_not_in_exception_message(client, query):
  responses_lib.add(responses_lib.GET, f'{_DEFAULT_ENDPOINT}/latest',
                    json={'message': 'Unauthorized'}, status=401)
  with pytest.raises(CurrencyApiClientError) as exc_info:
    client.get_response(query)
  assert 'test-key' not in str(exc_info.value)


@responses_lib.activate
def test_flattens_data_and_merges_meta(client, query, currency_payload):
  responses_lib.add(responses_lib.GET, f'{_DEFAULT_ENDPOINT}/latest', json=currency_payload)
  response = client.get_response(query)
  assert {r['code'] for r in response.results} == {'USD', 'GBP'}
  assert all(r.get('last_updated_at') == '2026-01-01T00:00:00Z' for r in response.results)


@responses_lib.activate
@pytest.mark.parametrize('payload', [
  {'data': {}},
  {'meta': {'last_updated_at': '2026-01-01T00:00:00Z'}},
])
def test_empty_or_missing_data_returns_empty(client, query, payload):
  responses_lib.add(responses_lib.GET, f'{_DEFAULT_ENDPOINT}/latest', json=payload)
  assert client.get_response(query).results == []


@responses_lib.activate
def test_raises_on_non_200(client, query):
  responses_lib.add(responses_lib.GET, f'{_DEFAULT_ENDPOINT}/latest',
                    json={'message': 'Unauthorized'}, status=401)
  with pytest.raises(CurrencyApiClientError):
    client.get_response(query)
