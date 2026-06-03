SELECT
  timestamp,
  instance,
  job,
  value
FROM query_range
WHERE
  query = up
  AND start=2026-06-03T00:00:30.781Z
  AND end=2026-06-03T20:11:00.781Z
  AND step = 15s
