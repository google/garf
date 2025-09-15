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
import os

import dotenv
from garf_youtube_data_api import api_clients, report_fetcher

dotenv.load_dotenv()

api_client = api_clients.YouTubeDataApiClient(
  api_key=os.getenv('YOUTUBE_DATA_API_KEY')
)
fetcher = report_fetcher.YouTubeDataApiReportFetcher(api_client=api_client)


def test_query_with_ids_only():
  query = 'SELECT id, snippet.title AS title FROM videos'
  test_youtube_id = os.getenv('YOUTUBE_ID')
  fetched_report = fetcher.fetch(query, id=[test_youtube_id])

  assert fetched_report[0].id == test_youtube_id


def test_query_with_ids_and_kwargs():
  query = (
    'SELECT id, player.embedWidth AS width, '
    'player.embedHeight AS height FROM videos'
  )
  test_youtube_id = os.getenv('YOUTUBE_ID')
  fetched_report = fetcher.fetch(query, id=[test_youtube_id], maxWidth=500)

  assert fetched_report[0].id == test_youtube_id


def test_query_with_kwargs_only_without_id():
  query = 'SELECT id, snippet.title FROM videos'
  fetched_report = fetcher.fetch(query, regionCode='US', chart='mostPopular')
  assert fetched_report[0]
