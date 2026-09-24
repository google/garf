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
import requests
import slack_sdk


class TelegramNotifier:
  """Sends report to Telegram chat."""

  def __init__(
    self, token: str | None = os.getenv('TELEGRAM_BOT_TOKEN')
  ) -> None:
    self._base_url = f'https://api.telegram.org/bot{token}'

  def act(
    self,
    report: garf.core.GarfReport,
    chat_id: str,
    title: str = 'garf-actors.csv',
    **kwargs: str,
  ):
    if not report:
      payload = {
        'chat_id': chat_id,
        'text': 'No results',
      }
      response = requests.post(f'{self._base_url}/sendMessage', json=payload)
    else:
      payload = {
        'chat_id': chat_id,
        'caption': title,
      }
      file_buffer = io.StringIO()
      report.to_pandas().to_csv(file_buffer, index=False)
      file_buffer.seek(0)
      files = {'document': (title, file_buffer.getvalue())}
      response = requests.post(
        f'{self._base_url}/sendDocument', data=payload, files=files
      )
    response.raise_for_status()


class SlackNotifier:
  """Sends report to Slack channel."""

  def __init__(self, bot_token: str | None = os.getenv('SLACK_BOT_TOKEN')):
    self.client = slack_sdk.WebClient(token=bot_token)

  def act(
    self,
    report: garf.core.GarfReport,
    channel: str,
    title: str = 'garf-actor-results.csv',
    **kwargs: str,
  ):
    if not report:
      self.client.chat_postMessage(
        channel=channel,
        text='No results',
      )
    else:
      csv_buffer = io.BytesIO()
      report.to_pandas().to_csv(csv_buffer, index=False)
      csv_buffer.seek(0)
      self.client.files_upload_v2(
        channel=channel,
        filename=title,
        file=csv_buffer.getvalue(),
        title=title,
      )
