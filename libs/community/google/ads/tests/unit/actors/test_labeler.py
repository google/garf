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
from garf.community.google.ads.actors import labeler


class TestLabeler:
  def test_plan_adds_new_labels(self, test_client):
    actor = labeler.Labeler(test_client)

    test_report = garf.core.GarfReport(
      results=[
        [1, 'label1', 'label3, label4'],
        [1, 'label2', 'label3, label4'],
        [1, 'label3', 'label3, label4'],
        [2, 'label4', 'label3, label4'],
      ],
      column_names=['customer_id', 'name', 'new_labels'],
    )
    operations, _ = actor.plan(report=test_report, workflow_name='labels')
    assert operations.get(1)[0].create.name == 'label4'
    assert operations.get(2)[0].create.name == 'label3'

  def test_add_labels(self, test_client):
    actor = labeler.Labeler(test_client)

    labels = ['test1', 'test2']
    existing_labels = {'test1': 1}
    operations = actor.add_labels(
      customer_id=1, labels=labels, existing_labels=existing_labels
    )
    operations = operations.get(1)
    assert operations[0].create.name == 'test2'

  def test_label_campaigns_existing_labels(self, test_client):
    actor = labeler.Labeler(test_client)
    campaign_ids = [1, 2]
    labels = ['test1', 'test2']

    operations = actor.label_campaigns(
      customer_id=1,
      campaign_ids=campaign_ids,
      labels=labels,
      existing_labels={'test1': 1, 'test2': 2},
    )
    operations = operations.get(1)
    assert len(operations) == len(campaign_ids) * len(labels)
    label = operations[0].create
    assert label.campaign == 'customers/1/campaigns/1'
    assert label.label == 'customers/1/labels/1'

  def test_label_campaigns_new_labels(self, test_client):
    actor = labeler.Labeler(test_client)
    campaign_ids = [1, 2]
    labels = ['test1', 'new_label']

    operations = actor.label_campaigns(
      customer_id=1,
      campaign_ids=campaign_ids,
      labels=labels,
      existing_labels={'test1': 1},
    )

    operations = operations.get(1)
    assert len(operations) == len(campaign_ids) * len(labels) + 1
    label_creation = operations[0].create
    assert label_creation.name == 'new_label'

    existing_label = operations[1].create
    assert existing_label.campaign == 'customers/1/campaigns/1'
    assert existing_label.label == 'customers/1/labels/1'

    temp_label = operations[-1].create
    assert temp_label.campaign == 'customers/1/campaigns/2'
    assert temp_label.label == 'customers/1/labels/-1'
