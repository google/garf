SELECT
  code,
  value AS rate
FROM latest
WHERE base_currency={base_currency}
  AND currencies={currencies}
