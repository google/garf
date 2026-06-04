SELECT
  timestamp,
  instance,
  job,
  value
FROM query_range
WHERE
  query = up
  AND start=2026-06-02
  AND end=2026-06-03
  AND step = 1h
