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

CREATE OR REPLACE TABLE `{bq_dataset}_bq.video_assets`
AS (
  WITH asset_group_with_videos AS(
    SELECT DISTINCT asset_group_id
    FROM `{bq_dataset}.video_assetgroup_assets`
    WHERE video_id IS NOT NULL
    AND video_id != ''
  ),
  count_videos AS (
    SELECT
        campaign_id,
        asset_group_id,
        COUNT(*) AS count_videos
    FROM `{bq_dataset}.video_assetgroup_assets`
    GROUP BY 1, 2
 ),
Mapping AS (
  SELECT
    asset_group_id,
    campaign_id,
    ANY_VALUE(asset_group_name) AS asset_group_name,
    ANY_VALUE(campaign_name) AS campaign_name,
    ANY_VALUE(account_id) AS account_id,
    ANY_VALUE(account_name) AS account_name,
    ANY_VALUE(ad_strength) AS ad_strength
  FROM `{bq_dataset}.assetgroupsummary`
  GROUP BY 1, 2
)
  SELECT DISTINCT
    AGS.account_id,
    AGS.account_name,
    AGS.campaign_id,
    AGS.campaign_name,
    AGS.asset_group_id,
    AGS.asset_group_name,
    AGS.ad_strength,
    IF(AGV.asset_group_id IS NULL, "X", "Yes") AS is_video_uploaded,
    COALESCE(CV.count_videos,0) AS count_videos
  FROM `{bq_dataset}.image_assetgroup_assets` AS IAS
    LEFT JOIN Mapping AS AGS
  USING (campaign_id, asset_group_id)
  LEFT JOIN asset_group_with_videos AS AGV USING (asset_group_id)
  LEFT JOIN count_videos CV USING (campaign_id,asset_group_id)
)
