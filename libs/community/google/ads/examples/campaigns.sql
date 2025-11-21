SELECT
"{current_date}" AS today,
campaign.id AS campaign_id,
campaign.name AS campaign_name,
metrics.cost_micros / 1e6 AS cost
FROM campaign
WHERE campaign.status = ENABLED
AND segments.date >= '{start_date}'
AND segments.date <= '{end_date}'
