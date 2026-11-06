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

CREATE OR REPLACE TABLE `{bq_dataset}_bq.assetssnapshots_{yesterday_iso}` AS (
WITH Mapping AS (
  SELECT
    asset_group_id,
    campaign_id,
    ANY_VALUE(asset_group_name) AS asset_group_name,
    ANY_VALUE(campaign_name) AS campaign_name,
    ANY_VALUE(account_id) AS account_id,
    ANY_VALUE(account_name) AS account_name
  FROM `{bq_dataset}.assetgroupsummary`
  GROUP BY 1, 2
),
Assets AS (
  SELECT
    campaign_id,
    asset_group_id,
    asset_id,
    asset_sub_type,
    text_asset_text,
    '' AS image_video,
    '' AS image_video_url
  FROM `{bq_dataset}.text_assetgroup_assets`
  GROUP BY ALL
  UNION ALL
  SELECT
    campaign_id,
    asset_group_id,
    asset_id,
    asset_sub_type,
    '' AS text_asset_text,
    image_url AS image_video,
    image_url AS image_video_url
  FROM `{bq_dataset}.image_assetgroup_assets`
  GROUP BY ALL
  UNION ALL
  SELECT
    campaign_id,
    asset_group_id,
    asset_id,
    asset_sub_type,
    '' AS text_asset_text,
    CONCAT('https://www.youtube.com/watch?v=', video_id) AS image_video,
    CONCAT('https://i.ytimg.com/vi/', CONCAT(video_id, '/hqdefault.jpg')) AS image_video_url
  FROM `{bq_dataset}.video_assetgroup_assets`
  GROUP BY ALL
)
SELECT
  CURRENT_DATE()-1 as day,
  AGA.account_id,
  AGA.account_name,
  AGA.asset_group_id,
  AGA.asset_group_name,
  AGA.campaign_name,
  AGA.campaign_id,
  A.asset_id,
  A.asset_sub_type,
  A.text_asset_text,
  A.image_video,
  A.image_video_url
FROM Mapping AS AGA
FULL JOIN Assets AS A
  USING (campaign_id, asset_group_id)
GROUP BY 1,2,3,4,5,6,7,8,9,10,11,12)
