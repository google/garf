-- Copyright 2026 Google LLC
--
-- Licensed under the Apache License, Version 2.0 (the "License");
-- you may not use this file except in compliance with the License.
-- You may obtain a copy of the License at
--
--     https://www.apache.org/licenses/LICENSE-2.0
--
-- Unless required by applicable law or agreed to in writing, software
-- distributed under the License is distributed on an "AS IS" BASIS,
-- WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
-- See the License for the specific language governing permissions and
-- limitations under the License.

-- Gets daily campaign costs for enable campaigns.

-- @param start_date First date of the period.
-- @param end_date Last date of the period.

SELECT
  segments.date AS date,
  campaign.id AS campaign_id,
  campaign.name AS campaign_name,
  metrics.cost_micros / 1e6 AS cost
FROM campaign
WHERE
  campaign.status = ENABLED
  AND segments.date >= '{start_date}'
  AND segments.date <= '{end_date}'
