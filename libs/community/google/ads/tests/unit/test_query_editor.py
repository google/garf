# Copyright 2025 Google LLC
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


from garf.community.google.ads.query_editor import GoogleAdsApiQuery


class TestGoogleAdsApiQuery:
  def test_generate(self):
    query = """
      SELECT
        campaign.type,
        ad_group_ad.policy_summary.policy_topic_entries:type
          AS policy_topic_type,
        ad_group_ad_asset_view.policy_summary:policy_topic_entries.type
          AS asset_policy_type
      FROM ad_group_ad_asset_view
    """
    spec = GoogleAdsApiQuery(text=query).generate()
    assert spec.fields == [
      'campaign.type_',
      'ad_group_ad.policy_summary.policy_topic_entries',
      'ad_group_ad_asset_view.policy_summary',
    ]
    assert spec.customizers.get('policy_topic_type').value == 'type_'
    assert (
      spec.customizers.get('asset_policy_type').value
      == 'policy_topic_entries.type_'
    )
