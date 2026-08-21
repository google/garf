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

import logging
from collections import defaultdict

from garf.community.google.ads.actors import base
from garf.community.google.ads.actors.models.label import Label
from garf.community.google.ads.actors.services import label as label_service
from google.ads.googleads.client import GoogleAdsClient

logger = logging.getLogger(__name__)

LABELS_QUERY = """
SELECT
  customer.id AS customer_id,
  label.id AS id,
  label.name AS name,
  label.text_label.description AS description,
  label.text_label.background_color AS color,
FROM label
WHERE
  label.status = ENABLED
"""


class Labeler(base.BaseActor):
  """Add labels to entities (Campaign, AdGroup, Keyword)."""

  def __init__(self, api_client: GoogleAdsClient | None = None) -> None:
    super().__init__(api_client=api_client)
    self.labeling_service = label_service.LabelService(client=self.client)

  def plan(self, report, workflow_name: str, **kwargs: str):
    if workflow_name == 'labels':
      operations = self._add_new_labels(report)
      return operations, self.labeling_service
    accounts = {r.customer_id for r in report}
    existing_labels = self.fetch(query=LABELS_QUERY, accounts=list(accounts))
    label_creation_operations = self._add_new_labels(existing_labels)
    if workflow_name == 'campaign_performance':
      service = label_service.CampaignLabelService(client=self.client)
      for row in report:
        labeling_operations = self.labels_campaigns(
          customer_id=row.customer_id,
          campaign_ids=[row.campaign_id],
          labels=row.labels,
          service=service,
          existing_labels=existing_labels,
        )
      return label_creation_operations + labeling_operations, service

    if workflow_name == 'ad_group_performance':
      service = label_service.AdGroupLabelService(client=self.client)
    elif workflow_name == 'keywords':
      service = label_service.AdGroupCriterionLabelService(client=self.client)
    return None

  def label_campaigns(
    self,
    customer_id: int,
    campaign_ids: list[int],
    labels: list[str],
    service: label_service.CampaignLabelService | None = None,
    existing_labels: dict[str, str] | None = None,
  ):
    """Adds labels to campaigns."""
    existing_labels = existing_labels or self.fetch(
      query=LABELS_QUERY, accounts=customer_id
    ).to_dict('label', 'id', value_column_output='scalar')
    service = service or label_service.CampaignLabelService(client=self.client)
    labels_to_create = [
      label for label in labels if label not in existing_labels
    ]
    operations = []
    temporarily_label_id = -1
    for label in labels:
      if not (label_id := existing_labels.get(label)):
        label_id = temporarily_label_id
        temporarily_label_id -= 1
      for campaign_id in campaign_ids:
        operations.append(
          service.add(
            customer_id=customer_id,
            campaign_id=campaign_id,
            label=Label(name=label, label_id=label_id),
          )
        )
    if labels_to_create:
      label_creation_operations = self.labeling_service.add(
        labels=[Label(name=label) for label in labels_to_create]
      )
      return {customer_id: label_creation_operations + operations}, service
    return operations, service

  def _add_new_labels(self, report):
    operations = defaultdict(list)
    new_labels = {label.strip() for label in report[0].new_labels.split(', ')}
    for customer_id, existing_labels in report.to_dict(
      key_column='customer_id',
      value_column='label',
      value_column_output='list',
    ).items():
      if labels_to_add := new_labels.difference(existing_labels):
        labels = [Label(name=label) for label in labels_to_add]
        operation = self.labeling_service.add(labels=labels)
        operations[customer_id].extend(operation)
    return operations

  def act(self, report, workflow_name: str, **kwargs: str):
    operations, service = self.plan(report, workflow_name, **kwargs)
    results = []
    for customer_id, ops in operations.items():
      if ops:
        results.extend(
          service.apply_operations(customer_id=customer_id, operations=ops)
        )
    return results
