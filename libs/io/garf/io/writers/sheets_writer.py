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
"""Module for writing data to Google Sheets."""

from __future__ import annotations

import logging
import re
import uuid
from typing import Any, Literal

try:
  import google.auth
  from google.oauth2 import service_account
  from googleapiclient.discovery import Resource, build
except ImportError as e:
  raise ImportError(
    'Please install garf-io with sheets support - `pip install garf-io[sheets]`'
  ) from e

from garf.core import report as garf_report
from garf.io import exceptions, formatter
from garf.io.telemetry import tracer
from garf.io.writers import google_api_utils
from garf.io.writers.abs_writer import AbsWriter
from opentelemetry import trace
from typing_extensions import override

logger = logging.getLogger(__name__)
logging.getLogger('googleapiclient.discovery_cache').setLevel(logging.ERROR)


class SheetsWriterError(exceptions.GarfIoError):
  """SheetsWriterError specific errors."""


class SheetsWriter(AbsWriter):
  """Writes garf Report to Google Sheets."""

  def __init__(
    self,
    share_with: str | list[str] | None = None,
    credentials_file: str | None = None,
    spreadsheet_url: str | None = None,
    auth_mode: Literal['oauth', 'service_account', 'adc'] = 'adc',
    is_append: bool = False,
    folder_id: str | None = None,
    spreadsheet_name: str | None = None,
    **kwargs: str,
  ) -> None:
    """Initializes the SheetsWriter to write reports to Google Sheets.

    Args:
      share_with: Email address to share the spreadsheet.
      credentials_file: Path to the service account credentials file.
      spreadsheet_url: URL of the Google Sheets spreadsheet.
      auth_mode:
        Type of authentication - OAuth2.0, Service Account,
        Application Default Credentials.
      is_append: Whether to append data to the spreadsheet.
      folder_id: Optional folder to add new spreadsheet to.
      spreadsheet_name: Optional name of a new spreadsheet.
      kwargs: Optional keyword arguments to initialize writer.
    """
    super().__init__(**kwargs)
    if isinstance(share_with, str):
      share_with = share_with.split(',')
    elif share_with is None:
      share_with = []
    self.share_with = share_with
    self.credentials_file = credentials_file
    self.spreadsheet_url = spreadsheet_url
    self.auth_mode = auth_mode
    self.is_append = is_append
    self.folder_id = folder_id
    self.spreadsheet_name = spreadsheet_name
    self._credentials = None
    self._client = None
    self._drive_service = None
    self.spreadsheet: dict[str, Any] | None = None
    self.spreadsheet_id: str | None = None

  @property
  def drive_service(self) -> Resource:
    """Google Drive API client."""
    if not self._drive_service:
      self._drive_service = build('drive', 'v3', credentials=self.credentials)
    return self._drive_service

  @override
  @tracer.start_as_current_span('sheets.write')
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
    )
    if not self.spreadsheet:
      self.create_or_get_spreadsheet()
    num_data_rows = len(report) + 1
    sheet = self._get_or_add_worksheet(
      destination, rows=num_data_rows, cols=len(report.column_names)
    )
    sheet_id = sheet['properties']['sheetId']
    if not self.is_append:
      self.client.spreadsheets().values().clear(
        spreadsheetId=self.spreadsheet_id,
        range=destination,
        body={},
      ).execute()
      self._add_rows_if_needed(num_data_rows, destination, sheet_id)
      self._append_rows(
        destination,
        [report.column_names] + report.results,
      )
    else:
      self._add_rows_if_needed(num_data_rows, destination, sheet_id)
      self._append_rows(destination, report.results)

    sheet_url = (
      f'https://docs.google.com/spreadsheets/d/{self.spreadsheet_id}'
      f'/edit#gid={sheet_id}'
    )
    logger.info('Report is saved to %s', sheet_url)
    return f'[Sheets] at {sheet_url}'

  @property
  def credentials(self):
    """Initialized Google API credentials."""
    span = trace.get_current_span()
    if self._credentials:
      return self._credentials
    scopes = [
      'https://www.googleapis.com/auth/spreadsheets',
      'https://www.googleapis.com/auth/drive',
    ]
    if not self.credentials_file:
      try:
        self._credentials, _ = google.auth.default(scopes=scopes)
        span.set_attribute('drive.auth_mode', 'adc')
      except Exception as e:
        raise SheetsWriterError(
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
      raise SheetsWriterError(f'Unknown auth_mode: {self.auth_mode}')
    return self._credentials

  @property
  @tracer.start_as_current_span('sheets.create_client')
  def client(self) -> Resource:
    """Google Sheets API client."""
    if not self._client:
      self._client = build('sheets', 'v4', credentials=self.credentials)
    return self._client

  @tracer.start_as_current_span('sheets.create_or_get_spreadsheet')
  def create_or_get_spreadsheet(self) -> dict[str, Any] | None:
    """Gets existing spreadsheet or creates a new one."""
    span = trace.get_current_span()
    if not self.spreadsheet_url:
      title = self.spreadsheet_name or f'Garf {uuid.uuid4().hex}'
      if self.folder_id:
        file_metadata: dict[str, Any] = {
          'name': title,
          'mimeType': 'application/vnd.google-apps.spreadsheet',
          'parents': [self.folder_id],
        }
        spreadsheet_file = (
          self.drive_service.files()
          .create(
            body=file_metadata,
            fields='id',
            supportsAllDrives=True,
          )
          .execute()
        )
        self.spreadsheet_id = spreadsheet_file.get('id')
        self.spreadsheet = (
          self.client.spreadsheets()
          .get(spreadsheetId=self.spreadsheet_id)
          .execute()
        )
      else:
        self.spreadsheet = (
          self.client.spreadsheets()
          .create(body={'properties': {'title': title}})
          .execute()
        )
        self.spreadsheet_id = self.spreadsheet.get('spreadsheetId')
      self.spreadsheet_url = self.spreadsheet.get('spreadsheetUrl')
      span.set_attribute('sheets.is_new_spreadsheet', True)
    else:
      self.spreadsheet_id = self._extract_spreadsheet_id(self.spreadsheet_url)
      self.spreadsheet = (
        self.client.spreadsheets()
        .get(spreadsheetId=self.spreadsheet_id)
        .execute()
      )
    if self.share_with:
      for email_address in self.share_with:
        self.drive_service.permissions().create(
          fileId=self.spreadsheet_id,
          body={
            'type': 'user',
            'role': 'writer',
            'emailAddress': email_address,
          },
          sendNotificationEmail=False,
          supportsAllDrives=True,
        ).execute()
    return self.spreadsheet

  def _extract_spreadsheet_id(self, spreadsheet_url: str) -> str:
    if match := re.search(r'/spreadsheets/d/([a-zA-Z0-9-_]+)', spreadsheet_url):
      return match.group(1)
    return spreadsheet_url

  def _get_or_add_worksheet(
    self, title: str, rows: int, cols: int
  ) -> dict[str, Any]:
    for sheet in self.spreadsheet.get('sheets', []):
      if sheet.get('properties', {}).get('title') == title:
        return sheet
    response = (
      self.client.spreadsheets()
      .batchUpdate(
        spreadsheetId=self.spreadsheet_id,
        body={
          'requests': [
            {
              'addSheet': {
                'properties': {
                  'title': title,
                  'gridProperties': {
                    'rowCount': rows,
                    'columnCount': cols,
                  },
                }
              }
            }
          ]
        },
      )
      .execute()
    )
    new_sheet = response['replies'][0]['addSheet']
    self.spreadsheet.setdefault('sheets', []).append(new_sheet)
    return new_sheet

  def _append_rows(
    self,
    destination: str,
    values: list[list[Any]],
  ) -> None:
    self.client.spreadsheets().values().append(
      spreadsheetId=self.spreadsheet_id,
      range=f'{destination}!A1',
      valueInputOption='RAW',
      body={'values': values},
    ).execute()

  def _add_rows_if_needed(
    self, num_data_rows: int, destination: str, sheet_id: int
  ) -> None:
    result = (
      self.client.spreadsheets()
      .values()
      .get(spreadsheetId=self.spreadsheet_id, range=destination)
      .execute()
    )
    num_sheet_rows = len(result.get('values', []))
    if num_data_rows > num_sheet_rows:
      num_rows_to_add = num_data_rows - num_sheet_rows
      self.client.spreadsheets().batchUpdate(
        spreadsheetId=self.spreadsheet_id,
        body={
          'requests': [
            {
              'appendDimension': {
                'sheetId': sheet_id,
                'dimension': 'ROWS',
                'length': num_rows_to_add,
              }
            }
          ]
        },
      ).execute()

  def __str__(self) -> str:
    """String representation of SheetsWriter."""
    return f'[Sheets] - data are saved to {self.spreadsheet_url}.'


SheetWriter = SheetsWriter
