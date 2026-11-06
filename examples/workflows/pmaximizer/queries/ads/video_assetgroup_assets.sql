SELECT
  segments.date AS date,
  campaign.id AS campaign_id,
  asset_group.id AS asset_group_id,
  asset.id AS asset_id,
  asset_group_asset.field_type AS asset_sub_type,
  asset.youtube_video_asset.youtube_video_id AS video_id,
  asset.youtube_video_asset.youtube_video_title AS video_title,
  metrics.cost_micros/1e6 AS cost,
  metrics.impressions AS impressions,
  metrics.clicks AS clicks,
  metrics.conversions AS conversions,
  metrics.conversions_value AS conversions_value
FROM asset_group_asset
WHERE campaign.advertising_channel_type = 'PERFORMANCE_MAX'
  AND campaign.status = 'ENABLED'
  AND asset_group.status = 'ENABLED'
  AND asset_group_asset.status = 'ENABLED'
  AND asset_group_asset.source = 'ADVERTISER'
  AND segments.date >= '{start_date}'
  AND segments.date <= '{end_date}'
  AND asset.type = 'YOUTUBE_VIDEO'
