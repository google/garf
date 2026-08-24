# Copyright 2026 Google LLC
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

import garf.core
from garf.community.google.ads.actors import adder


class TestAdder:
  def test_plan_new_text(self, test_client):
    test_report = garf.core.GarfReport(
      results=[
        [1, 'test1'],
      ],
      column_names=['customer_id', 'text'],
    )

    operations, _ = adder.Adder(test_client).plan(
      report=test_report, workflow_name='texts'
    )
    asset = operations[1][0].create
    assert asset.type_.name == 'TEXT'
    assert asset.text_asset.text == 'test1'

  def test_plan_new_video(self, test_client):
    test_report = garf.core.GarfReport(
      results=[
        [1, '12345678900', 'test'],
      ],
      column_names=['customer_id', 'video_id', 'title'],
    )

    operations, _ = adder.Adder(test_client).plan(
      report=test_report, workflow_name='videos'
    )

    asset = operations[1][0].create
    assert asset.type_.name == 'YOUTUBE_VIDEO'
    assert asset.youtube_video_asset.youtube_video_id == '12345678900'
    assert asset.youtube_video_asset.youtube_video_title == 'test'

  def test_plan_new_sitelink(self, test_client):
    test_report = garf.core.GarfReport(
      results=[
        [
          1,
          'test_title',
          'https://test.com',
          'test_description1',
          'test_description2',
        ],
      ],
      column_names=[
        'customer_id',
        'sitelink',
        'url',
        'description1',
        'description2',
      ],
    )

    operations, _ = adder.Adder(test_client).plan(
      report=test_report, workflow_name='sitelinks'
    )

    asset = operations[1][0].create
    assert asset.type_.name == 'SITELINK'
    assert asset.sitelink_asset.link_text == 'test_title'
    assert asset.sitelink_asset.description1 == 'test_description1'
    assert asset.sitelink_asset.description2 == 'test_description2'
    assert asset.final_urls == ['https://test.com/']
