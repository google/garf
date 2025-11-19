# Copyright 2025 Google LLC
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

"""Stores and loads reports from a cache instead of calling API."""

from __future__ import annotations

import datetime
import hashlib
import json
import logging
import os
import pathlib
from typing import Final

from garf_core import exceptions, query_editor, report

logger = logging.getLogger(__name__)


class GarfCacheFileNotFoundError(exceptions.GarfError):
  """Exception for not found cached report."""


DEFAULT_CACHE_LOCATION: Final[str] = os.getenv(
  'GARF_CACHE_LOCATION', str(pathlib.Path.home() / '.garf/cache/')
)


class GarfCache:
  """Stores and loads reports from a cache instead of calling API.

  Attribute:
    location: Folder where cached results are stored.
  """

  def __init__(
    self,
    location: str | None = None,
    ttl_seconds: int = 3600,
  ) -> None:
    """Stores and loads reports from a cache instead of calling API.

    Args:
      location: Folder where cached results are stored.
      ttl_seconds: Maximum lifespan of cached objects.
    """
    self.location = pathlib.Path(location or DEFAULT_CACHE_LOCATION)
    self.ttl_seconds = ttl_seconds

  @property
  def max_cache_timestamp(self) -> float:
    return (
      datetime.datetime.now() - datetime.timedelta(seconds=self.ttl_seconds)
    ).timestamp()

  def load(
    self, query: query_editor.BaseQueryElements, args=None, kwargs=None
  ) -> report.GarfReport:
    """Loads report from cache based on query definition.

    Args:
      query: Query elements.
      args: Query parameters.
      kwargs: Optional keyword arguments.

    Returns:
      Cached report.

    Raises:
      GarfCacheFileNotFoundError: If cached report not found
    """
    args_hash = args.hash if args else ''
    kwargs_hash = (
      hashlib.md5(json.dumps(kwargs).encode('utf-8')).hexdigest()
      if kwargs
      else ''
    )
    hash_identifier = f'{query.hash}:{args_hash}:{kwargs_hash}'
    cached_path = self.location / f'{hash_identifier}.json'
    if (
      cached_path.exists()
      and cached_path.stat().st_ctime > self.max_cache_timestamp
    ):
      with open(cached_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
      logger.debug('Report is loaded from cache: %s', str(cached_path))
      return report.GarfReport.from_json(data)
    raise GarfCacheFileNotFoundError

  def save(
    self,
    fetched_report: report.GarfReport,
    query: query_editor.BaseQueryElements,
    args=None,
    kwargs=None,
  ) -> None:
    """Saves report to cache based on query definition.

    Args:
      fetched_report: Report to save.
      query: Query elements.
      args: Query parameters.
      kwargs: Optional keyword arguments.
    """
    self.location.mkdir(parents=True, exist_ok=True)
    args_hash = args.hash if args else ''
    kwargs_hash = (
      hashlib.md5(json.dumps(kwargs).encode('utf-8')).hexdigest()
      if kwargs
      else ''
    )
    hash_identifier = f'{query.hash}:{args_hash}:{kwargs_hash}'
    cached_path = self.location / f'{hash_identifier}.json'
    logger.debug('Report is saved to cache: %s', str(cached_path))
    with open(cached_path, 'w', encoding='utf-8') as f:
      json.dump(fetched_report.to_json(), f)
