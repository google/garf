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

from garf.community.google.ads.actors.models.label import Label
from garf.community.google.ads.actors.services import base_service


class LabelService(base_service.BaseService):
  """Creates new labels."""

  def add(self, labels: list[Label]) -> list:
    """Converts new labels to operations."""
    return [label.to_operation(self.client) for label in labels]

  def apply_operations(self, customer_id, operations):
    """Adds labels to account."""
    service = self.client.get_service('LabelService')
    response = service.mutate_labels(
      customer_id=customer_id,
      operations=operations,
    )
    return [result.resource_name for result in response.results]


class CustomerLabelService(base_service.BaseService):
  """Handles labeling accounts."""

  def add(self, customer_id: int, label: Label):
    """Add existing labels to account."""
    operation = self.client.get_type('CustomerLabelOperation')
    customer_label = operation.create
    customer_resource_name = f'customer/{customer_id}'
    label_resource_name = f'customer/{customer_id}/labels/{label.label_id}'
    customer_label.customer = customer_resource_name
    customer_label.label = label_resource_name
    return operation

  def apply_operations(self, customer_id, operations):
    """Adds labels to account."""
    service = self.client.get_service('CustomerLabelService')
    response = service.mutate_customer_labels(
      customer_id=customer_id,
      operations=operations,
    )
    return [result.resource_name for result in response.results]


class CampaignLabelService(base_service.BaseService):
  """Handles labeling campaigns."""

  def add(self, customer_id: int, campaign_id: int, label: Label):
    """Add existing labels to campaign."""
    operation = self.client.get_type('CampaignLabelOperation')
    campaign_label = operation.create
    campaign_resource_name = f'customer/{customer_id}/campaigns/{campaign_id}'
    label_resource_name = f'customer/{customer_id}/labels/{label.label_id}'
    campaign_label.campaign = campaign_resource_name
    campaign_label.label = label_resource_name
    return operation

  def apply_operations(self, customer_id, operations):
    """Adds labels to campaign."""
    service = self.client.get_service('CampaignLabelService')
    response = service.mutate_campaign_labels(
      customer_id=customer_id,
      operations=operations,
    )
    return [result.resource_name for result in response.results]


class AdGroupAdLabelService(base_service.BaseService):
  """Handles labeling ad group ads."""

  def add(self, customer_id: int, ad_group_id: int, ad_id: str, label: Label):
    """Add existing labels to ad_group_ad."""
    operation = self.client.get_type('AdGroupAdLabelOperation')
    ad_group_ad_label = operation.create
    ad_group_ad_resource_name = (
      f'customer/{customer_id}/adGroupAds/{ad_group_id}~{ad_id}'
    )
    label_resource_name = f'customer/{customer_id}/labels/{label.label_id}'
    ad_group_ad_label.ad_group_ad = ad_group_ad_resource_name
    ad_group_ad_label.label = label_resource_name
    return operation

  def apply_operations(self, customer_id, operations):
    """Adds labels to campaign."""
    service = self.client.get_service('AdGroupAdLabelService')
    response = service.mutate_ad_group_ad_labels(
      customer_id=customer_id,
      operations=operations,
    )
    return [result.resource_name for result in response.results]


class AdGroupLabelService(base_service.BaseService):
  """Handles labeling ad group ads."""

  def add_label_to_ad_group(
    self, customer_id: int, ad_group_id: int, label: Label
  ):
    """Add existing labels to ad_group."""
    operation = self.client.get_type('AdGroupLabelOperation')
    ad_group_label = operation.create
    ad_group_resource_name = f'customer/{customer_id}/adGroups/{ad_group_id}'
    label_resource_name = f'customer/{customer_id}/labels/{label.label_id}'
    ad_group_label.ad_group = ad_group_resource_name
    ad_group_label.label = label_resource_name
    return operation

  def apply_operations(self, customer_id, operations):
    """Adds labels to campaign."""
    service = self.client.get_service('AdGroupLabelService')
    response = service.mutate_ad_group_labels(
      customer_id=customer_id,
      operations=operations,
    )
    return [result.resource_name for result in response.results]


class AdGroupCriterionLabelService(base_service.BaseService):
  """Handles labeling ad group criteria."""

  def add(
    self, customer_id: int, ad_group_id: int, criterion_id: str, label: Label
  ):
    """Add existing labels to ad group criterion."""
    operation = self.client.get_type('AdGroupCriterionLabelOperation')
    ad_group_criterion_label = operation.create
    ad_group_criterion_resource_name = (
      f'customer/{customer_id}/adGroupCriteria/{ad_group_id}~{criterion_id}'
    )
    label_resource_name = f'customer/{customer_id}/labels/{label.label_id}'
    ad_group_criterion_label.ad_group_criterion = (
      ad_group_criterion_resource_name
    )
    ad_group_criterion_label.label = label_resource_name
    return operation

  def apply_operations(self, customer_id, operations):
    """Adds labels to ad group ad criteria."""
    service = self.client.get_service('AdGroupCriterionLabelService')
    response = service.mutate_ad_group_criterion_labels(
      customer_id=customer_id,
      operations=operations,
    )
    return [result.resource_name for result in response.results]
