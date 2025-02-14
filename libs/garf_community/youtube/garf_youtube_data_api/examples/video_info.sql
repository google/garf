-- Copyright 2025 Google LLC
--
-- Licensed under the Apache License, Version 2.0 (the "License");
-- you may not use this file except in compliance with the License.
-- You may obtain a copy of the License at
--
--     https://www.apache.org/licenses/LICENSE-2.0
--
-- Unless required by applicable law or agreed to in writing, software
-- distributed under the License is distributed on an "AS IS" BASIS,
-- WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
-- See the License for the specific language governing permissions and
-- limitations under the License.

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
  contentDetails.caption AS has_caption
FROM videos
