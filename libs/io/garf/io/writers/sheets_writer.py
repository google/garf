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

from google.auth import exceptions as auth_exceptions

try:
  import gspread
except ImportError as e:
  raise ImportError(
    'Please install garf-io with sheets support - `pip install garf-io[sheets]`'
  ) from e

import logging
import pathlib
import uuid

from garf.core import report as garf_report
from garf.io import exceptions, formatter
from garf.io.telemetry import tracer
from garf.io.writers.abs_writer import AbsWriter
from opentelemetry import trace
from typing_extensions import override

logger = logging.getLogger(__name__)


class SheetWriterError(exceptions.GarfIoError):
  """SheetWriterError specific errors."""


class SheetWriter(AbsWriter):
  """Responsible for writing reports to Google Sheets."""

  def __init__(
    self,
    share_with: str | list[str] | None = None,
    credentials_file: str | None = None,
    spreadsheet_url: str | None = None,
    is_append: bool = False,
    **kwargs: str,
  ) -> None:
    """Initializes the SheetWriter to write reports to Google Sheets.

    Args:
      share_with: Email address to share the spreadsheet.
      credentials_file: Path to the service account credentials file.
      spreadsheet_url: URL of the Google Sheets spreadsheet.
      is_append: Whether you want to append data to the spreadsheet.
      spreadsheet: Initialized and shared spreadsheet.
    """
    super().__init__(**kwargs)
    if isinstance(share_with, str):
      share_with = share_with.split(',')
    elif share_with is None:
      share_with = []
    self.share_with = share_with
    self.credentials_file = credentials_file
    self.spreadsheet_url = spreadsheet_url
    self.is_append = is_append
    self._client = None

  @override
  @tracer.start_as_current_span('sheets.write')
  def write(
    self,
    report: garf_report.GarfReport,
    destination: str = f'Report {uuid.uuid4().hex}',
  ) -> str:
    report = self.format_for_write(report)
    if not destination:
      destination = f'Report {uuid.uuid4().hex}'
    destination = formatter.format_extension(destination)
    num_data_rows = len(report) + 1
    try:
      sheet = self.spreadsheet.worksheet(destination)
    except gspread.exceptions.WorksheetNotFound:
      sheet = self.spreadsheet.add_worksheet(
        destination, rows=num_data_rows, cols=len(report.column_names)
      )
    if not self.is_append:
      sheet.clear()
      self._add_rows_if_needed(num_data_rows, sheet)
      sheet.append_rows(
        [report.column_names] + report.results, value_input_option='RAW'
      )
    else:
      self._add_rows_if_needed(num_data_rows, sheet)
      sheet.append_rows(report.results, value_input_option='RAW')

    success_msg = f'Report is saved to {sheet.url}'
    logger.info(success_msg)
    return success_msg

  @property
  @tracer.start_as_current_span('sheets.create_client')
  def client(self) -> gspread.Client:
    span = trace.get_current_span()
    if self._client:
      return self._client
    config_dir = pathlib.Path.home() / '.config/gspread'
    if not self.credentials_file:
      if (credentials_file := config_dir / 'credentials.json').is_file():
        self._client = gspread.oauth(credentials_filename=credentials_file)
        span.set_attribute('sheets.auth_mode', 'oauth')
      elif (credentials_file := config_dir / 'service_account.json').is_file():
        self._client = self._init_service_account(credentials_file)
        span.set_attribute('sheets.auth_mode', 'service_account')
      else:
        raise SheetWriterError(
          'Failed to find either service_accounts.json or '
          'credentials.json files.'
          'Provide path to service account via `credentials_file` option'
        )
    else:
      try:
        self._client = self._init_service_account(self.credential_file)
      except auth_exceptions.MalformedError:
        self._client = gspread.oauth(credentials_filename=self.credentials_file)
    return self._client

  def _init_service_account(
    self, credentials_file: str | pathlib.Path
  ) -> gspread.Client:
    client = gspread.service_account(filename=credentials_file)
    if not self.spreadsheet_url:
      raise SheetWriterError(
        'Provide `spreadsheet_url` parameter when working with '
        'service account authentication.'
      )
    return client

  @tracer.start_as_current_span('sheets.create_or_get_spreadsheet')
  def create_or_get_spreadsheet(self) -> gspread.spreadsheet.Spreadsheet:
    span = trace.get_current_span()
    if not self.spreadsheet_url:
      spreadsheet = self.client.create(title=f'Garf {uuid.uuid4().hex}')
      span.set_attribute('sheets.is_new_spreadsheet', True)
      if not self.share_with:
        raise SheetWriterError('Provide your email in `share_with` parameter')
    else:
      spreadsheet = self.client.open_by_url(self.spreadsheet_url)
    if self.share_with:
      for email_address in self.share_with:
        spreadsheet.share(
          email_address=email_address,
          perm_type='user',
          role='writer',
          notify=False,
        )
    self.spreadsheet = spreadsheet
    return self.spreadsheet

  def _add_rows_if_needed(
    self, num_data_rows: int, sheet: gspread.worksheet.Worksheet
  ) -> None:
    num_sheet_rows = len(sheet.get_all_values())
    if num_data_rows > num_sheet_rows:
      num_rows_to_add = num_data_rows - num_sheet_rows
      sheet.add_rows(num_rows_to_add)

  def __str__(self) -> str:
    return f'[Sheet] - data are saved to {self.spreadsheet_url}.'
