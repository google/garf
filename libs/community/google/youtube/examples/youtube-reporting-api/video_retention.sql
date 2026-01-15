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
