SELECT
  dimension.country AS country,
  metric.activeUsers AS users
FROM resource
WHERE
  start_date >= "2025-09-01"
  AND end_date <= "2025-09-07"
