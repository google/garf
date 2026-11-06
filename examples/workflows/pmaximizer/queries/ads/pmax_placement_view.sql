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
    segments.date AS date,
    campaign.status AS _,
    campaign.advertising_channel_type AS _,
    campaign.id,
    performance_max_placement_view.display_name AS placement_name,
    performance_max_placement_view.placement AS placement,
    performance_max_placement_view.placement_type AS placement_type,
    performance_max_placement_view.target_url AS placement_target_url,
    metrics.impressions AS impressions
FROM performance_max_placement_view
WHERE campaign.advertising_channel_type = PERFORMANCE_MAX
    AND segments.date >= "{start_date}"
    AND segments.date <= "{end_date}"
    AND campaign.status = ENABLED
    AND metrics.impressions > 10
ORDER BY metrics.impressions DESC, segments.date DESC
LIMIT 10000
