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

import pytest
from google.ads.googleads.client import GoogleAdsClient


@pytest.fixture
def test_client(mocker):
  mocker.patch('google.ads.googleads.client.oauth2', return_value=[])
  dummy_config = {
    'developer_token': 'abcd123efg',
    'client_id': 'dummy_id',
    'client_secret': 'dummy_secret',
    'refresh_token': 'dummy_refresh',
    'use_proto_plus': True,
  }

  return GoogleAdsClient.load_from_dict(dummy_config)
