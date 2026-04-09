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

-- Gets normalized target bids for each active campaign.

SELECT
  campaign.id AS campaign_id,
  campaign.bidding_strategy_type AS bidding_strategy,
  campaign.target_cpa.target_cpa_micros / 1e6 AS target_cpa,
  campaign.target_roas.target_roas AS target_roas,
  campaign.target_roas.cpc_bid_floor_micros / 1e6 AS target_roas_cpc_bid_floor,
  campaign.target_roas.cpc_bid_ceiling_micros / 1e6 AS target_roas_cpc_bid_ceiling,
  campaign.target_cpc.target_cpc_micros / 1e6 AS target_cpc,
  campaign.maximize_conversion_value.target_roas AS maximize_conversion_value_target_roas,
  campaign.maximize_conversions.target_cpa_micros / 1e6 AS maximize_conversion_target_cpa
FROM campaign
WHERE campaign.status = ENABLED
