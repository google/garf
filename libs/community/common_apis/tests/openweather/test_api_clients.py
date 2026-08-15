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

"""Tests for OpenWeatherApiClient."""

import pytest
import responses as responses_lib
from garf.community.common_apis.openweather.api_clients import (
  OpenWeatherApiClient,
  OpenWeatherApiClientError,
  _DEFAULT_ENDPOINT,
)
from garf.core.query_editor import BaseQueryElements


@pytest.fixture
def query():
  return BaseQueryElements(
    title=None,
    text='SELECT main.temp FROM weather WHERE lat=33.44 AND lon=-94.04',
    resource_name='weather',
    fields=['main.temp'],
    filters=['lat=33.44', 'lon=-94.04'],
    column_names=['temperature'],
  )


@pytest.fixture
def client():
  return OpenWeatherApiClient(api_key='test-key')


@pytest.fixture
def weather_payload():
  return {
    'name': 'TestCity',
    'main': {'temp': 295, 'humidity': 60},
    'weather': [{'main': 'Clear', 'description': 'clear sky'}],
  }


@pytest.mark.parametrize('bad_key', ['', None])
def test_raises_on_missing_api_key(bad_key):
  with pytest.raises(OpenWeatherApiClientError, match='API key'):
    OpenWeatherApiClient(api_key=bad_key)


def test_api_key_not_stored_in_query_args():
  c = OpenWeatherApiClient(api_key='secret-key')
  assert 'secret-key' not in str(c.query_args)


@responses_lib.activate
def test_injects_api_key_as_appid_param(client, query, weather_payload):
  responses_lib.add(responses_lib.GET, f'{_DEFAULT_ENDPOINT}/weather', json=weather_payload)
  client.get_response(query)
  assert 'appid=test-key' in responses_lib.calls[0].request.url


@responses_lib.activate
def test_api_key_not_in_exception_message(client, query):
  responses_lib.add(responses_lib.GET, f'{_DEFAULT_ENDPOINT}/weather', status=401,
                    json={'message': 'Invalid API key.'})
  with pytest.raises(OpenWeatherApiClientError) as exc_info:
    client.get_response(query)
  assert 'test-key' not in str(exc_info.value)


@responses_lib.activate
def test_filters_passed_as_query_params(client, query, weather_payload):
  responses_lib.add(responses_lib.GET, f'{_DEFAULT_ENDPOINT}/weather', json=weather_payload)
  client.get_response(query)
  url = responses_lib.calls[0].request.url
  assert 'lat=33.44' in url
  assert 'lon=-94.04' in url


@responses_lib.activate
def test_object_response_wrapped_in_list(client, query, weather_payload):
  responses_lib.add(responses_lib.GET, f'{_DEFAULT_ENDPOINT}/weather', json=weather_payload)
  response = client.get_response(query)
  assert len(response.results) == 1
  assert response.results[0]['name'] == 'TestCity'


@responses_lib.activate
def test_raises_on_non_200(client, query):
  responses_lib.add(responses_lib.GET, f'{_DEFAULT_ENDPOINT}/weather',
                    json={'message': 'not found'}, status=404)
  with pytest.raises(OpenWeatherApiClientError):
    client.get_response(query)
