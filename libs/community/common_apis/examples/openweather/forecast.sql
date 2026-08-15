SELECT
  dt_txt AS datetime,
  main.temp AS temperature_kelvin,
  main.humidity AS humidity_pct,
  weather[0].main AS conditions,
  pop AS precipitation_probability
FROM forecast
WHERE lat={lat}
  AND lon={lon}
  AND cnt={count}
