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

from __future__ import annotations

import json
import pathlib

from google.auth.exceptions import RefreshError
from google.auth.transport.requests import Request
from google.oauth2 import credentials as oauth_credentials
from google_auth_oauthlib.flow import InstalledAppFlow


def init_oauth(
  credentials_file: str | pathlib.Path,
  scopes: list[str],
) -> oauth_credentials.Credentials:
  credentials_path = pathlib.Path(credentials_file).expanduser()
  with credentials_path.open(encoding='utf-8') as f:
    cred_data = json.load(f)

  if 'installed' not in cred_data and 'web' not in cred_data:
    creds = oauth_credentials.Credentials.from_authorized_user_info(
      cred_data, scopes=scopes
    )
    if creds.expired and creds.refresh_token:
      creds.refresh(Request())
    return creds

  client_config = cred_data.get('installed') or cred_data.get('web') or {}
  client_id = client_config.get('client_id')
  authorized_user_path = pathlib.Path.home() / '.garf/authorized_user.json'
  creds = None
  if authorized_user_path.is_file():
    try:
      with authorized_user_path.open(encoding='utf-8') as f:
        auth_user_data = json.load(f)
      if not client_id or auth_user_data.get('client_id') == client_id:
        creds = oauth_credentials.Credentials.from_authorized_user_info(
          auth_user_data, scopes=scopes
        )
    except (ValueError, KeyError):
      creds = None

  if not creds or not creds.valid:
    if creds and creds.expired and creds.refresh_token:
      try:
        creds.refresh(Request())
      except RefreshError:
        creds = None
    if not creds:
      flow = InstalledAppFlow.from_client_secrets_file(
        str(credentials_path), scopes=scopes
      )
      creds = flow.run_local_server(port=0)
    authorized_user_path.parent.mkdir(parents=True, exist_ok=True)
    authorized_user_path.write_text(creds.to_json(), encoding='utf-8')
  return creds
