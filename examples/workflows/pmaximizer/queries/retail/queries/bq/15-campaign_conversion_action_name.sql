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



CREATE OR REPLACE TABLE `{bq_dataset}_bq.campaign_conversion_action_name` AS (
  WITH Mapping AS (
    SELECT
      campaign_id,
      ANY_VALUE(campaign_name) AS campaign_name,
      ANY_VALUE(account_name) AS account_name,
      ANY_VALUE(account_id) AS account_id,
    FROM `{bq_dataset}.campaign_settings`
    GROUP BY 1
  )
  SELECT
    date,
    M.account_id,
    M.account_name,
    M.campaign_id,
    M.campaign_name,
    C.conversion_action_name,
    C.conversion_action_category,
    SUM(C.all_conversions) AS all_conversions,
    SUM(C.all_conversions_value) AS all_conversions_value,
    SUM(C.conversions) AS conversions,
    SUM(C.view_through_conversions) AS view_thrupgh_conversions,
    SUM(C.value_per_conversion) AS value_per_conversion
  FROM `{bq_dataset}.campaignconversionaction` AS C
  LEFT JOIN Mapping AS M USING (campaign_id)
  GROUP BY 1, 2, 3, 4, 5, 6, 7
);
