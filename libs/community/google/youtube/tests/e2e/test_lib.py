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
from garf.community.google.youtube import api_clients, report_fetcher

dotenv.load_dotenv()

api_client = api_clients.YouTubeDataApiClient()
fetcher = report_fetcher.YouTubeDataApiReportFetcher(api_client=api_client)


def test_query_with_non_existing_id_returns_empty_report():
  query = 'SELECT id, snippet.title AS title FROM videos'
  test_youtube_id = 'no-existing-video-id'
  fetched_report = fetcher.fetch(query, id=[test_youtube_id])
  assert not fetched_report


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


def test_builtin_channel_videos_with_enhanced_attributes():
  """Test that builtin.channelVideos returns enhanced video attributes."""
  query = """
    SELECT
        channel_id,
        video_id,
        title,
        description,
        published_at,
        view_count,
        like_count,
        comment_count,
        duration,
        privacy_status
    FROM builtin.channelVideos
    """

  test_channel_id = os.getenv('YOUTUBE_CHANNEL_ID', 'UCmMowAX5A4tYd4Utq1Lymog')

  fetched_report = fetcher.fetch(query, id=[test_channel_id])

  assert fetched_report
  assert fetched_report.column_names == [
    'channel_id',
    'video_id',
    'title',
    'description',
    'published_at',
    'view_count',
    'like_count',
    'comment_count',
    'duration',
    'privacy_status',
  ]

  assert fetched_report[0].channel_id == test_channel_id
