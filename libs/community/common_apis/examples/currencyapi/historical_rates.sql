SELECT
  code,
  value AS rate
FROM historical
WHERE date={date}
  AND base_currency={base_currency}
  AND currencies={currencies}
