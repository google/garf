SELECT
  timestamp,
  sum by(job) (rate(scrape_duration_seconds[1h])) AS scrape_rate
FROM query
