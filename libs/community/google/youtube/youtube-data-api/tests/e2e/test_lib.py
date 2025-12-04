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
    query = '''
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
    '''

    # Use a test channel ID from environment
    test_channel_id = os.getenv('YOUTUBE_CHANNEL_ID', 'UC_x5XG1OV2P6uZZ5FSM9Ttw')

    fetched_report = fetcher.fetch(query, id=[test_channel_id])

    # Verify we got results
    assert fetched_report, "No videos returned from channelVideos"
    assert len(fetched_report) > 0, "channelVideos returned empty list"

    # Verify the enhanced attributes are present in the first video
    first_video = fetched_report[0]
    assert hasattr(first_video, 'channel_id'), "Missing channel_id attribute"
    assert hasattr(first_video, 'video_id'), "Missing video_id attribute"
    assert hasattr(first_video, 'title'), "Missing title attribute"
    assert hasattr(first_video, 'view_count'), "Missing view_count attribute"
    assert hasattr(first_video, 'duration'), "Missing duration attribute"

    # Verify the values are not None/empty
    assert first_video.video_id, "video_id is empty"
    assert first_video.title, "title is empty"

    print(f"✓ channelVideos test passed! Found {len(fetched_report)} videos")
    print(f"  First video: {first_video.title}")
    print(f"  Video ID: {first_video.video_id}")
    if hasattr(first_video, 'view_count') and first_video.view_count:
        print(f"  Views: {first_video.view_count}")