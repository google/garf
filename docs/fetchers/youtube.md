The `garf-youtube` library provides a unified way to interact with various YouTube APIs, streamlining data fetching and reporting within the `garf` framework. It acts as an umbrella library, allowing you to access both the YouTube Data API and the YouTube Analytics API through consistent `garf` queries.

## Overview

`garf-youtube` simplifies fetching data from YouTube by abstracting away the underlying API complexities. You can write SQL-like queries to specify the data you need, and `garf` handles the interaction with the appropriate YouTube API endpoint.

## Installation

To use `garf-youtube`, you typically install it along with `garf-executors`:

/// tab | pip
```bash
pip install garf-executors garf-youtube
```
///

/// tab | uv
```bash
uv pip install garf-executors garf-youtube
```
///

`garf-youtube` acts as a facade for the YouTube Data API and YouTube Analytics API. Depending on your query, `garf` will automatically route the request to the correct underlying fetcher.

## YouTube Data API
### Prerequisites

* [YouTube Data API](https://console.cloud.google.com/apis/library/youtube.googleapis.com) enabled.
* [API key](https://support.google.com/googleapi/answer/6158862?hl=en) to access to access YouTube Data API exposed as `export GARF_YOUTUBE_DATA_API_KEY=<YOUR_API_KEY>`

/// tab | cli
```bash
echo "SELECT id, snippet.title AS channel_name FROM channels" > query.sql
garf query.sql --source youtube-data-api \
  --output csv \
  --source.id=YOUTUBE_CHANNEL_ID
```
///

/// tab | python

```python
from garf.io import writer
from garf.community.google.youtube import YouTubeDataApiReportFetcher

query = 'SELECT id, snippet.title AS channel_name FROM channels'

fetched_report = (
  YouTubeDataApiReportFetcher()
  .fetch(query, id=[YOUTUBE_CHANNEL_ID])
)

csv_writer = writer.create_writer('csv')
csv_writer.write(fetched_report, 'query')
```
///

###  Available source parameters

| name | values| comments |
|----- | ----- | -------- |
| `id`   | id(s) of YouTube channels or videos | Multiple ids are supported, should be comma-separated|
| `forHandle` | YouTube channel handle | i.e. @myChannel |
| `forUsername` | YouTube channel name | i.e. myChannel |
| `regionCode` | ISO 3166-1 alpha-2 country code | i.e. US |
| `chart` | `mostPopular` | Gets most popular in `regionCode`, can be narrowed down with `videoCategoriId` |
| `videoId` | id(s) of YouTube Video to get comments from | Multiple ids are supported, should be comma-separated |

### Examples

#### Videos

**Gets meta information and statistics for YouTube videos.**

/// tab | cli
```bash
echo "
SELECT
  id,
  snippet.publishedAt AS published_at,
  snippet.title AS title,
  snippet.description AS description,
  snippet.channelTitle AS channel,
  snippet.tags AS tags,
  snippet.defaultLanguage AS language,
  snippet.defaultAudioLanguage AS audio_language,
  status.madeForKids AS made_for_kids,
  topicDetails.topicCategories AS topics,
  contentDetails.duration AS duration,
  contentDetails.caption AS has_caption,
  statistics.viewCount AS views,
  statistics.likeCount AS likes,
  statistics.commentCount AS comments,
  statistics.favoriteCount AS favourites
FROM videos
" > video_info.sql

garf video_info.sql --source youtube-data-api \
  --output csv \
  --source.id=YOUTUBE_VIDEO_ID_1,YOUTUBE_VIDEO_ID_2
```
///

/// tab | python

```python
from garf.io import writer
from garf.community.google.youtube import YouTubeDataApiReportFetcher

query = """
SELECT
  id,
  snippet.publishedAt AS published_at,
  snippet.title AS title,
  snippet.description AS description,
  snippet.channelTitle AS channel,
  snippet.tags AS tags,
  snippet.defaultLanguage AS language,
  snippet.defaultAudioLanguage AS audio_language,
  status.madeForKids AS made_for_kids,
  topicDetails.topicCategories AS topics,
  contentDetails.duration AS duration,
  contentDetails.caption AS has_caption,
  statistics.viewCount AS views,
  statistics.likeCount AS likes,
  statistics.commentCount AS comments,
  statistics.favoriteCount AS favourites
FROM videos
"""

fetched_report = (
  YouTubeDataApiReportFetcher()
  .fetch(query, id=[YOUTUBE_VIDEO_ID_1, YOUTUBE_VIDEO_ID_2])
)

csv_writer = writer.create_writer('csv')
csv_writer.write(fetched_report, 'video_info')
```
///

**Gets YouTube video(s) height and width.**

/// tab | cli
```bash hl_lines="12"
echo "
SELECT
  id,
  player.embedWidth AS width,
  player.embedHeight AS height
FROM videos
" > video_orientation.sql

garf video_orientation.sql --source youtube-data-api \
  --output csv \
  --source.id=YOUTUBE_VIDEO_ID_1,YOUTUBE_VIDEO_ID_2 \
  --source.maxWidth=500
```
///

/// tab | python

```python hl_lines="19"
from garf.io import writer
from garf.community.google.youtube import YouTubeDataApiReportFetcher

query = """
SELECT
  id,
  player.embedWidth AS width,
  player.embedHeight AS height
FROM videos
"""

fetched_report = (
  YouTubeDataApiReportFetcher()
  .fetch(
    query,
    id=[YOUTUBE_VIDEO_ID_1, YOUTUBE_VIDEO_ID_2],
    maxWidth=500
  )
)

csv_writer = writer.create_writer('csv')
csv_writer.write(fetched_report, 'video_orientation')
```
///

#### Channels

**Gets meta information and statistics for YouTube channel(s).**

/// tab | cli
```bash
echo "
SELECT
  id,
  snippet.title AS title,
  snippet.description AS description,
  snippet.publishedAt AS published_at,
  snippet.country AS country,
  snippet.defaultLanguage AS language,
  status.madeForKids AS made_for_kids,
  topicDetails.topicCategories AS topics,
  statistics.videoCount AS videos,
  statistics.viewCount AS views,
  statistics.subscriberCount AS subscribers
FROM channels
" > channel_info.sql

garf channel_info.sql --source youtube-data-api \
  --output csv \
  --source.id=YOUTUBE_CHANNEL_ID
```
///

/// tab | python

```python
from garf.io import writer
from garf.community.google.youtube import YouTubeDataApiReportFetcher

query = """
SELECT
  id,
  snippet.title AS title,
  snippet.description AS description,
  snippet.publishedAt AS published_at,
  snippet.country AS country,
  snippet.defaultLanguage AS language,
  status.madeForKids AS made_for_kids,
  topicDetails.topicCategories AS topics,
  statistics.videoCount AS videos,
  statistics.viewCount AS views,
  statistics.subscriberCount AS subscribers
FROM channels
"""

fetched_report = (
  YouTubeDataApiReportFetcher()
  .fetch(query, id=[YOUTUBE_CHANNEL_ID])
)

csv_writer = writer.create_writer('csv')
csv_writer.write(fetched_report, 'channel_info')
```
///


**Gets all public videos from YouTube channel(s)**

/// tab | cli
```bash
echo "
SELECT
  channel_id,
  video_id
FROM builtin.channelVideos
" > channel_videos.sql

garf channel_videos.sql --source youtube-data-api \
  --output csv \
  --source.id=YOUTUBE_CHANNEL_ID
```
///

/// tab | python

```python
from garf.io import writer
from garf.community.google.youtube import YouTubeDataApiReportFetcher

query = """
SELECT
  channel_id,
  video_id
FROM builtin.channelVideos
"""

fetched_report = (
  YouTubeDataApiReportFetcher()
  .fetch(query, id=[YOUTUBE_CHANNEL_ID])
)

csv_writer = writer.create_writer('csv')
csv_writer.write(fetched_report, 'channel_videos')
```
///

#### Commentaries

**Gets tops level commentaries for YouTube video(s).**

/// tab | cli
```bash
echo "
SELECT
  id AS commentary_id,
  snippet.videoId AS video_id,
  snippet.topLevelComment.snippet.textDisplay AS comment
FROM commentThreads
" > video_commentaries.sql

garf video_commentaries.sql --source youtube-data-api \
  --output csv \
  --source.id=YOUTUBE_VIDEO_ID_1,YOUTUBE_VIDEO_ID_2
```
///

/// tab | python

```python
from garf.io import writer
from garf.community.google.youtube import YouTubeDataApiReportFetcher


query = """
SELECT
  id AS commentary_id,
  snippet.videoId AS video_id,
  snippet.topLevelComment.snippet.textDisplay AS comment
FROM commentThreads
"""

fetched_report = (
  YouTubeDataApiReportFetcher()
  .fetch(query, id=[YOUTUBE_VIDEO_ID_1, YOUTUBE_VIDEO_ID_2])
)

csv_writer = writer.create_writer('csv')
csv_writer.write(fetched_report, 'video_commentaries')
```
///

## YouTube Analytics API

### Prerequisites

* [YouTube Reporting API](https://console.cloud.google.com/apis/library/youtubereporting.googleapis.com) enabled.
* [Client ID, client secret](https://support.google.com/cloud/answer/6158849?hl=en) and refresh token generated.
!!!important
    Please note you'll need to use *Web application* OAuth2 credentials type and set "https://developers.google.com/oauthplayground" as redirect url in it.

* Refresh token. You can use [OAuth Playground](https://developers.google.com/oauthplayground/) to generate refresh token.
    * Select `https://www.googleapis.com/auth/yt-analytics.readonly` scope
    * Enter OAuth Client ID and OAuth Client secret under *Use your own OAuth credentials*;
    * Click on *Authorize APIs*

* Expose client id,  client secret and refresh token as environmental variables:

/// tab | cli
```bash
echo """
SELECT
  dimensions.day AS date,
  metrics.views AS views
FROM channel
WHERE
  channel==MINE
  AND startDate = 2025-01-01
  AND endDate = 2025-12-31
" > query.sql

garf query.sql --source youtube-analytics \
  --output csv
```
///

/// tab | Python

```python
from garf.io import writer
from garf.community.google.youtube import YouTubeAnalyticsApiReportFetcher

query = """
SELECT
  dimensions.day AS date,
  metrics.views AS views
FROM channel
WHERE
  channel==MINE
  AND startDate = 2025-01-01
  AND endDate = 2025-12-31
"""

fetched_report = (
  YouTubeAnalyticsApiReportFetcher()
  .fetch(query)
)

csv_writer = writer.create_writer('csv')
csv_writer.write(fetched_report, 'report_data')
```
///

### Examples

#### Channel views

**Gets daily number of views for a channel.**

/// tab | cli
```bash
echo "
SELECT
  dimensions.day AS date,
  metrics.views AS views
FROM channel
WHERE
  channel==MINE
  AND startDate = {start_date}
  AND endDate = {end_date}
" > channel_daily_views.sql

garf channel_daily_views.sql --source youtube-analytics \
  --output csv \
  --macro.start_date=2025-01-01 \
  --macro.end_date=2025-12-31
```
///

/// tab | python

```python
from garf.io import writer
from garf.community.google.youtube import YouTubeAnalyticsApiReportFetcher

query = """
SELECT
  dimensions.day AS date,
  metrics.views AS views
FROM channel
WHERE
  channel==MINE
  AND startDate = {start_date}
  AND endDate = {end_date}
"""

fetched_report = (
  YouTubeAnalyticsApiReportFetcher()
  .fetch(
    query,
    args={
      'start_date': '2025-01-01',
      'end_date': '2025-12-31',
    }
  )
)

csv_writer = writer.create_writer('csv')
csv_writer.write(fetched_report, 'channel_daily_views')
```
///

#### Video retention

**Gets retention information for a given video.**

/// tab | cli
```bash
echo "
SELECT
  dimensions.elapsedVideoTimeRatio AS time_ratio,
  metrics.audienceWatchRatio AS watch_ratio,
  metrics.relativeRetentionPerformance AS retention
FROM channel
WHERE
  channel==MINE
  AND audienceType==ORGANIC
  AND video=={video_id}
  AND startDate = {start_date}
  AND endDate = {end_date}
" > video_retention.sql

garf video_retention.sql --source youtube-analytics \
  --output csv \
  --macro.video_id=YOUTUBE_VIDEO_ID \
  --macro.start_date=2025-01-01 \
  --macro.end_date=2025-12-31
```
///

/// tab | python

```python
from garf.io import writer
from garf.community.google.youtube import YouTubeAnalyticsApiReportFetcher

query = """
SELECT
  dimensions.elapsedVideoTimeRatio AS time_ratio,
  metrics.audienceWatchRatio AS watch_ratio,
  metrics.relativeRetentionPerformance AS retention
FROM channel
WHERE
  channel==MINE
  AND audienceType==ORGANIC
  AND video=={video_id}
  AND startDate = {start_date}
  AND endDate = {end_date}
"""

fetched_report = (
  YouTubeAnalyticsApiReportFetcher()
  .fetch(
    query,
    args={
      'video_id': YOUTUBE_VIDEO_ID,
      'start_date': '2025-01-01',
      'end_date': '2025-12-31',
    }
  )
)

csv_writer = writer.create_writer('csv')
csv_writer.write(fetched_report, 'video_retention')
```
///
