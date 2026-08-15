SELECT
  name AS city,
  sys.country AS country,
  main.temp AS temperature_kelvin,
  main.feels_like AS feels_like_kelvin,
  main.humidity AS humidity_pct,
  weather[0].main AS conditions,
  weather[0].description AS description,
  wind.speed AS wind_speed_ms
FROM weather
WHERE lat={lat}
  AND lon={lon}
