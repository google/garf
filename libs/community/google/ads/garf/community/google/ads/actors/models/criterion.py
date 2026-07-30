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

import pydantic
from google.ads.googleads.client import GoogleAdsClient
from typing_extensions import override


class CriterionError(Exception):
  """Criterion errors."""


class Criterion(pydantic.BaseModel):
  """Criterion."""

  negative: bool = False

  def to_operation(self, client: GoogleAdsClient, operation_name: str):
    """Converts models to a corresponding mutate operation.

    Args:
      client: Initialized Google Ads client.
      operation_name: Name of operation.
    """
    raise NotImplementedError


class Keyword(Criterion):
  text: str = pydantic.Field(min_length=1, max_length=80)
  match_type: str = 'EXACT'

  def model_post_init(self, __context):
    if (num_words := len(self.text.split(' '))) > 10:
      raise CriterionError(
        f'Keyword must contain maximum 10 words, got {num_words}: {self.text}'
      )

  def to_operation(self, client, operation_name):
    criterion_operation = client.get_type(operation_name)
    criterion = criterion_operation.create
    criterion.keyword.text = self.text
    criterion.keyword.match_type = getattr(
      client.enums.KeywordMatchTypeEnum, self.match_type
    )
    if self.negative and operation_name != 'CustomerNegativeCriterionOperation':
      criterion.negative = True
    return criterion_operation


class Placement(Criterion):
  type: str
  placement: str

  @override
  def to_operation(self, client, operation_name):
    criterion_operation = client.get_type(operation_name)
    criterion = criterion_operation.create
    if self.type == 'WEBSITE':
      criterion.placement.url = self._format_website(self.placement)
    if self.type == 'MOBILE_APPLICATION':
      criterion.mobile_application.app_id = self._format_app_id(self.placement)
    if self.type == 'YOUTUBE_VIDEO':
      criterion.youtube_video.video_id = self.placement
    if self.type == 'YOUTUBE_CHANNEL':
      criterion.youtube_channel.channel_id = self.placement
    if self.negative and operation_name != 'CustomerNegativeCriterionOperation':
      criterion.negative = True
    return criterion_operation

  def _format_app_id(self, app_id: str) -> str:
    """Returns app_id as acceptable negative criterion."""
    if app_id.startswith('mobileapp::'):
      criteria = app_id.split('-')
      app_id = criteria[-1]
      app_store = criteria[0].split('::')[-1]
      app_store = app_store.replace('mobileapp::1000', '')
      app_store = app_store.replace('1000', '')
      return f'{app_store}-{app_id}'
    return app_id

  def _format_website(self, website_url: str) -> str:
    """Returns website as acceptable negative criterion."""
    return website_url.split('/')[0]
