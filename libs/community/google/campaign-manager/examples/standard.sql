SELECT
  dimensions.advertiser AS advertiser,
  advertiserId AS advertiser_id,
  metrics.clicks AS clicks
FROM standard
WHERE dateRange IN (2026-05-01, 2026-05-02)
