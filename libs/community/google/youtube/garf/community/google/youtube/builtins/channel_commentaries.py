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
"""Fetches top level commentaries for all videos in the channel."""


def get_youtube_channel_commentaries(
  report_fetcher: 'garf.community.google.youtube.report_fetcher.YouTubeDataApiReportFetcher',
  **kwargs: str,
):
  if 'id' not in kwargs and 'channelId' in kwargs:
    kwargs['id'] = kwargs.pop('channelId')

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
  video_ids = report_fetcher.fetch(
    channel_videos_query,
    playlistId=','.join(
      videos_playlist.to_list(row_type='scalar', distinct=True)
    ),
    maxResults=50,
  ).to_list(row_type='scalar', distinct=True)

  video_comment_count_query = """
    SELECT
      id AS video_id,
      statistics.commentCount AS comments
    FROM videos
  """
  videos = report_fetcher.fetch(video_comment_count_query, id=video_ids)

  videos_with_comments = {v.video_id for v in videos if v.comments > 0}
  query = """
    SELECT
      id AS commentary_id,
      snippet.videoId AS video_id,
      snippet.topLevelComment.snippet.authorDisplayName AS author,
      snippet.topLevelComment.snippet.publishedAt AS published_at,
      snippet.topLevelComment.snippet.likeCount AS likes,
      snippet.topLevelComment.snippet.textDisplay AS comment,
    FROM commentThreads
  """
  return report_fetcher.fetch(query, videoId=list(videos_with_comments))
