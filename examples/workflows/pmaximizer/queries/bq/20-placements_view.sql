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

CREATE OR REPLACE TABLE `{bq_dataset}_bq.placements_view` AS (
  WITH Mapping AS (
    SELECT
      campaign_id,
      ANY_VALUE(campaign_name) AS campaign_name,
      ANY_VALUE(campaign_status) AS campaign_status,
      ANY_VALUE(account_name) AS account_name,
      ANY_VALUE(account_id) AS account_id,
    FROM `{bq_dataset}.campaign_settings`
    GROUP BY 1
  )
  SELECT
    P.date,
    'PERFORMANCE_MAX' AS campaign_type,
    M.campaign_status,
    M.account_id,
    M.account_name,
    M.campaign_id,
    M.campaign_name,
    P.placement_name,
    P.placement,
    P.placement_type,
    P.placement_target_url,
    P.impressions
  FROM `{bq_dataset}.pmax_placement_view` AS P
  LEFT JOIN Mapping AS M USING (campaign_id)
);
