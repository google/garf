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
"""Fetches mapping between channel_id and its videos."""


def get_youtube_channel_videos(
  report_fetcher: 'garf.community.google.youtube.report_fetcher.YouTubeDataApiReportFetcher',
  **kwargs: str,
):
  channel_uploads_playlist_query = """
    SELECT
      contentDetails.relatedPlaylists.uploads AS uploads_playlist
    FROM channels
    """
  videos_playlist = report_fetcher.fetch(
    channel_uploads_playlist_query, **kwargs
  )

  channel_videos_query = """
    SELECT
      contentDetails.videoId AS video_id
    FROM playlistItems
    """
  videos = report_fetcher.fetch(
    channel_videos_query,
    playlistId=videos_playlist.to_list(row_type='scalar', distinct=True),
    maxResults=50,
  ).to_list(row_type='scalar', distinct=True)

  video_performance_query = """
    SELECT
      snippet.channelId AS channel_id,
      id AS video_id,
      snippet.title AS title,
      snippet.description AS description,
      snippet.publishedAt AS published_at,
      snippet.categoryId AS category_id,
      snippet.defaultLanguage AS default_language,
      contentDetails.duration AS duration,
      contentDetails.definition AS definition,
      contentDetails.dimension AS dimension,
      contentDetails.caption AS caption,
      statistics.viewCount AS view_count,
      statistics.likeCount AS like_count,
      statistics.commentCount AS comment_count,
      statistics.favoriteCount AS favorite_count,
      status.uploadStatus AS upload_status,
      status.privacyStatus AS privacy_status,
      status.license AS license,
      status.embeddable AS embeddable,
      status.publicStatsViewable AS public_stats_viewable
    FROM videos
    """
  return report_fetcher.fetch(video_performance_query, id=videos)
