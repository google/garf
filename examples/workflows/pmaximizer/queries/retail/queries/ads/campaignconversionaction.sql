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


SELECT
    segments.date as date,
    campaign.id as campaign_id,
    segments.conversion_action_category as conversion_action_category,
    segments.conversion_action_name as conversion_action_name,
    metrics.all_conversions as all_conversions,
    metrics.all_conversions_value as all_conversions_value,
    metrics.conversions as conversions,
    metrics.value_per_conversion as value_per_conversion,
    metrics.view_through_conversions as view_through_conversions
FROM campaign
WHERE campaign.advertising_channel_type = "PERFORMANCE_MAX"
AND segments.date >= "{start_date}"
AND segments.date <= "{end_date}"
AND campaign.status = 'ENABLED'
