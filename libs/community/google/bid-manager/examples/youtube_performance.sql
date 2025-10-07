SELECT
  date AS date,
  youtube_ad_video_id AS media_url,
  youtube_ad_video AS media_name,
  metric_impressions AS impressions,
  metric_clicks AS clicks
FROM youtube
WHERE advertiser = {advertiser_id}
AND dataRange = LAST_30_DAYS
