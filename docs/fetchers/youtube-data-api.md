# garf for YouTube Data API

Interacts with [YouTube Data API](https://developers.google.com/youtube/v3/docs).

## Install

Install `garf-youtube-data-api` library

/// tab | pip
```
pip install garf-executors garf-youtube-data-api
```
///

/// tab | uv
```
uv add garf-executors garf-youtube-data-api
```
///

## Usage

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
import os

from garf_io import writer
from garf_youtube_data_api import YouTubeDataApiReportFetcher

query = 'SELECT id, snippet.title AS channel_name FROM channels'

fetched_report = (
  YouTubeDataApiReportFetcher(api_key=os.getenv('GARF_YOUTUBE_DATA_API_KEY'))
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

## Examples

### Videos

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
import os

from garf_io import writer
from garf_youtube_data_api import YouTubeDataApiReportFetcher

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
  YouTubeDataApiReportFetcher(api_key=os.getenv('GARF_YOUTUBE_DATA_API_KEY'))
  .fetch(query, id=[YOUTUBE_VIDEO_ID_1, YOUTUBE_VIDEO_ID_2])
)

csv_writer = writer.create_writer('csv')
csv_writer.write(fetched_report, 'video_info')
```
///



### Channels

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
import os

from garf_io import writer
from garf_youtube_data_api import YouTubeDataApiReportFetcher

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
  YouTubeDataApiReportFetcher(api_key=os.getenv('GARF_YOUTUBE_DATA_API_KEY'))
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
import os

from garf_io import writer
from garf_youtube_data_api import YouTubeDataApiReportFetcher

query = """
SELECT
  channel_id,
  video_id
FROM builtin.channelVideos
"""

fetched_report = (
  YouTubeDataApiReportFetcher(api_key=os.getenv('GARF_YOUTUBE_DATA_API_KEY'))
  .fetch(query, id=[YOUTUBE_CHANNEL_ID])
)

csv_writer = writer.create_writer('csv')
csv_writer.write(fetched_report, 'channel_videos')
```
///

### Commentaries

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
import os

from garf_io import writer
from garf_youtube_data_api import YouTubeDataApiReportFetcher


query = """
SELECT
  id AS commentary_id,
  snippet.videoId AS video_id,
  snippet.topLevelComment.snippet.textDisplay AS comment
FROM commentThreads
"""

fetched_report = (
  YouTubeDataApiReportFetcher(api_key=os.getenv('GARF_YOUTUBE_DATA_API_KEY'))
  .fetch(query, id=[YOUTUBE_VIDEO_ID_1, YOUTUBE_VIDEO_ID_2])
)

csv_writer = writer.create_writer('csv')
csv_writer.write(fetched_report, 'video_commentaries')
```
///
