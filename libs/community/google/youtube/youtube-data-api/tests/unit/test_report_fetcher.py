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

import garf_core
import pytest
from garf_youtube_data_api.report_fetcher import YouTubeDataApiReportFetcher


class TestYouTubeDataApiReportFetcher:
  @pytest.fixture
  def fetcher(self):
    return YouTubeDataApiReportFetcher()

  def test_fetch_returns_filtered_data(self, mocker, fetcher):
    query = """
      SELECT
        id,
        statistics.viewCount AS views,
        statistics.likeCount AS likes,
        snippet.publishedAt AS published_at,
      FROM videos
      WHERE
        snippet.publishedAt > 2025-01-01
        AND statistics.viewCount = 11
        AND statistics.likeCount > 1
    """

    mocker.patch(
      'garf_youtube_data_api.api_clients.YouTubeDataApiClient._list',
      return_value={
        'items': [
          {
            'id': 1,
            'statistics': {'viewCount': 10, 'likeCount': 1},
            'snippet': {'publishedAt': '2024-07-10T22:15:44Z'},
          },
          {
            'id': 2,
            'statistics': {'viewCount': 11, 'likeCount': 2},
            'snippet': {'publishedAt': '2025-07-10T22:15:44Z'},
          },
        ],
      },
    )

    result = fetcher.fetch(query, id=['1', '2'])
    expected_report = garf_core.GarfReport(
      results=[[2, 11, 2, '2025-07-10T22:15:44Z']],
      column_names=['id', 'views', 'likes', 'published_at'],
    )

    assert result == expected_report

  def test_fetch_returns_sorted_data(self, mocker, fetcher):
    query = """
      SELECT
        id,
        statistics.viewCount AS views,
        statistics.likeCount AS likes,
        snippet.publishedAt AS published_at,
      FROM videos
      ORDER BY likes DESC
    """

    mocker.patch(
      'garf_youtube_data_api.api_clients.YouTubeDataApiClient._list',
      return_value={
        'items': [
          {
            'id': 1,
            'statistics': {'viewCount': 10, 'likeCount': 1},
            'snippet': {'publishedAt': '2024-07-10T22:15:44Z'},
          },
          {
            'id': 2,
            'statistics': {'viewCount': 11, 'likeCount': 2},
            'snippet': {'publishedAt': '2025-07-10T22:15:44Z'},
          },
        ],
      },
    )

    result = fetcher.fetch(query, id=['1', '2'])
    expected_report = garf_core.GarfReport(
      results=[
        [2, 11, 2, '2025-07-10T22:15:44Z'],
        [1, 10, 1, '2024-07-10T22:15:44Z'],
      ],
      column_names=['id', 'views', 'likes', 'published_at'],
    )

    assert result == expected_report

  def test_fetch_returns_placeholder_data(self, mocker, fetcher):
    query = """
      SELECT
        id,
        statistics.viewCount AS views,
        statistics.likeCount AS likes,
        snippet.publishedAt AS published_at,
      FROM videos
      ORDER BY likes DESC
    """

    mocker.patch(
      'garf_youtube_data_api.api_clients.YouTubeDataApiClient._list',
      return_value={'items': []},
    )

    result = fetcher.fetch(query, id=['1'])
    expected_report = garf_core.GarfReport(
      results_placeholder=[
        ['', 1, 1, '1970-01-01'],
      ],
      column_names=['id', 'views', 'likes', 'published_at'],
    )

    assert (result.results_placeholder, result.column_names) == (
      expected_report.results_placeholder,
      expected_report.column_names,
    )
