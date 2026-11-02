# Copyright 2022 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

CREATE OR REPLACE TABLE `{bq_dataset}_bq.summaryassets` AS (
WITH Assets AS (
  SELECT
    date,
    campaign_id,
    asset_group_id,
    asset_id,
    asset_sub_type,
    text_asset_text,
    '' AS image_video,
    '' AS image_video_url,
    SUM(cost) AS cost,
    SUM(impressions) AS impressions,
    SUM(clicks) AS clicks,
    SUM(conversions) AS conversions,
    SUM(conversions_value) AS conversions_value
  FROM `{bq_dataset}.text_assetgroup_assets`
  GROUP BY ALL
  UNION ALL
  SELECT
    date,
    campaign_id,
    asset_group_id,
    asset_id,
    asset_sub_type,
    '' AS text_asset_text,
    image_url AS image_video,
    image_url AS image_video_url,
    SUM(cost) AS cost,
    SUM(impressions) AS impressions,
    SUM(clicks) AS clicks,
    SUM(conversions) AS conversions,
    SUM(conversions_value) AS conversions_value
  FROM `{bq_dataset}.image_assetgroup_assets`
  GROUP BY ALL
  UNION ALL
  SELECT
    date,
    campaign_id,
    asset_group_id,
    asset_id,
    asset_sub_type,
    '' AS text_asset_text,
    CONCAT('https://www.youtube.com/watch?v=', video_id) AS image_video,
    CONCAT('https://i.ytimg.com/vi/', CONCAT(video_id, '/hqdefault.jpg')) AS image_video_url,
    SUM(cost) AS cost,
    SUM(impressions) AS impressions,
    SUM(clicks) AS clicks,
    SUM(conversions) AS conversions,
    SUM(conversions_value) AS conversions_value
  FROM `{bq_dataset}.video_assetgroup_assets`
  GROUP BY ALL
),
Mapping AS (
  SELECT
    asset_group_id,
    campaign_id,
    ANY_VALUE(asset_group_name) AS asset_group_name,
    ANY_VALUE(campaign_name) AS campaign_name,
    ANY_VALUE(account_id) AS account_id,
    ANY_VALUE(account_name) AS account_name,
    ANY_VALUE(asset_group_status) AS asset_group_status
  FROM `{bq_dataset}.assetgroupsummary`
  GROUP BY 1, 2
)

SELECT
  AGA.date,
  AGS.account_id,
  AGS.account_name,
  AGS.asset_group_id,
  AGS.asset_group_name,
  AGS.campaign_name,
  AGS.campaign_id,
  AGA.asset_id,
  AGA.asset_sub_type,
  AGA.text_asset_text,
  AGS.asset_group_status,
  AGA.image_video,
  AGA.image_video_url,
  OCID.ocid,
  CS.last_30_day_campaign_cost,
  AGA.cost,
  AGA.impressions,
  AGA.clicks,
  AGA.conversions,
  AGA.conversions_value
FROM Assets AS AGA
JOIN Mapping AS AGS
  USING (campaign_id, asset_group_id)
LEFT JOIN `{bq_dataset}.ocid_mapping` AS OCID
  ON OCID.account_id = AGS.account_id
LEFT JOIN (
  SELECT
    campaign_id,
    SUM(cost) AS last_30_day_campaign_cost
  FROM `{bq_dataset}.campaign_settings`
  WHERE PARSE_DATE('%Y-%m-%d', date) >= DATE_SUB(CURRENT_DATE(),  INTERVAL 30 DAY)
  GROUP BY campaign_id
    ) AS CS ON AGA.campaign_id = CS.campaign_id
WHERE AGA.campaign_id
    IN (SELECT campaign_id FROM `{bq_dataset}.campaign_settings`)
GROUP BY ALL);
