SELECT
youtube_ad_video_id AS video_id,
youtube_ad_video AS video_name,
metric_clicks AS clicks,
FROM youtube
WHERE advertiser = {advertiser_id}
AND dataRange = LAST_7_DAYS
