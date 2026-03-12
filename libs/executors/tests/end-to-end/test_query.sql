SELECT
  resource,
  dimensions.name AS name,
  dimensions.values AS values,
  metrics.clicks AS clicks
FROM resource
