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
"""Module for writing data to Google Drive."""

from __future__ import annotations

import csv
import io
import logging
from typing import Any

try:
  import google.auth
  from google.oauth2 import service_account
  from googleapiclient.discovery import Resource, build
  from googleapiclient.http import MediaIoBaseUpload
except ImportError as e:
  raise ImportError(
    'Please install garf-io with Google Drive support - '
    '`pip install garf-io[drive]`'
  ) from e

from typing import Literal

from garf.core import report as garf_report
from garf.io import exceptions, formatter
from garf.io.telemetry import tracer
from garf.io.writers import google_api_utils
from garf.io.writers.abs_writer import AbsWriter
from opentelemetry import trace
from typing_extensions import override

logger = logging.getLogger(__name__)
logging.getLogger('googleapiclient.discovery_cache').setLevel(logging.ERROR)


class GoogleDriveWriterError(exceptions.GarfIoError):
  """GoogleDriveWriterError specific errors."""


class GoogleDriveWriter(AbsWriter):
  """Responsible for writing reports to Google Drive."""

  def __init__(
    self,
    folder_id: str,
    share_with: str | list[str] | None = None,
    credentials_file: str | None = None,
    auth_mode: Literal['oauth', 'service_account', 'adc'] = 'adc',
    **kwargs: str,
  ) -> None:
    """Initializes the GoogleDriveWriter.

    Args:
      folder_id: Optional folder to add new spreadsheet to.
      share_with: Email address to share the file.
      credentials_file: Path to the service account credentials file.
      auth_mode:
        Type of authentication - OAuth2.0, Service Account,
        Application Default Credentials.
      kwargs: Optional keyword arguments to initialize writer.
    """
    super().__init__(**kwargs)
    if isinstance(share_with, str):
      share_with = share_with.split(',')
    elif share_with is None:
      share_with = []
    self.share_with = share_with
    self.credentials_file = credentials_file
    self.folder_id = folder_id
    self.auth_mode = auth_mode
    self._credentials = None
    self._drive_service = None

  @property
  def drive_service(self) -> Resource:
    """Google Drive API client."""
    if not self._drive_service:
      self._drive_service = build('drive', 'v3', credentials=self.credentials)
    return self._drive_service

  @property
  def credentials(self):
    """Initialized Google API credentials."""
    span = trace.get_current_span()
    if self._credentials:
      return self._credentials
    scopes = ['https://www.googleapis.com/auth/drive']
    if not self.credentials_file:
      try:
        self._credentials, _ = google.auth.default(scopes=scopes)
        span.set_attribute('drive.auth_mode', 'adc')
      except Exception as e:
        raise GoogleDriveWriterError(
          'Failed to authorize with Google Application Default credentials. '
          'Provide `credentials_file` to perform authorization. '
        ) from e
    elif self.auth_mode == 'service_account':
      self._credentials = service_account.Credentials.from_service_account_file(
        str(self.credentials_file), scopes=scopes
      )
    elif self.auth_mode == 'oauth':
      self._credentials = google_api_utils.init_oauth(
        self.credentials_file, scopes=scopes
      )
    elif self.auth_mode == 'adc':
      credentials, _ = google.auth.default(scopes=scopes)
      self._credentials = credentials
    else:
      raise GoogleDriveWriterError(f'Unknown auth_mode: {self.auth_mode}')
    return self._credentials

  @override
  @tracer.start_as_current_span('drive.write')
  def write(
    self,
    report: garf_report.GarfReport,
    destination: str,
  ) -> str:
    report = self.format_for_write(report)
    destination = formatter.format_extension(
      destination,
      prefix=self.options.prefix,
      suffix=self.options.suffix,
      new_extension='.csv',
    )
    string_buffer = io.StringIO()
    csv_writer = csv.writer(string_buffer)
    csv_writer.writerow(report.column_names)
    csv_writer.writerows(report.results)
    string_buffer.seek(0)
    file_metadata: dict[str, Any] = {
      'name': destination,
      'mimeType': 'text/csv',
    }
    if self.folder_id:
      file_metadata['parents'] = [self.folder_id]

    media = MediaIoBaseUpload(
      io.BytesIO(string_buffer.getvalue().encode('utf-8')),
      mimetype='text/csv',
      resumable=True,
    )
    uploaded_file = (
      self.drive_service.files()
      .create(
        body=file_metadata,
        media_body=media,
        fields='id',
        supportsAllDrives=True,
      )
      .execute()
    )
    return '[Google Drive] at ' + uploaded_file.get('id')

  def __str__(self) -> str:
    """String representation of GoogleDriveWriter."""
    return (
      '[Google Drive] at '
      + f'https://drive.google.com/drive/u/0/folders/{self.folder_id}'
    )
