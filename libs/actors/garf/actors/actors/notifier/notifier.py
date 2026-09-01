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

"""Sends report via notification channel."""

import io
import os

import garf.core
import slack_sdk


class SlackNotifier:
  """Sends report to Slack channel."""

  def __init__(self, bot_token: str | None = os.getenv('SLACK_BOT_TOKEN')):
    self.client = slack_sdk.WebClient(token=bot_token)

  def act(
    self,
    report: garf.core.GarfReport,
    channel: str,
    title: str = 'garf-actors',
    **kwargs: str,
  ):
    if not report:
      self.client.chat_postMessage(
        channel=channel,
        text=title,
      )
    else:
      csv_buffer = io.BytesIO()
      report.to_pandas().to_csv(csv_buffer, index=False)
      csv_buffer.seek(0)
      self.client.files_upload_v2(
        channel=channel,
        filename='garf-actor-results.csv',
        file=csv_buffer.getvalue(),
        title=title,
      )
