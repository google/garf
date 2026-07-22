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
import shutil
from typing import Final

import redis
import smart_open
from garf.core import exceptions, query_editor, report

logger = logging.getLogger(__name__)


class GarfCacheFileNotFoundError(exceptions.GarfError):
  """Exception for not found cached report."""


DEFAULT_CACHE_LOCATION: Final[str] = os.getenv(
  'GARF_CACHE_LOCATION', str(pathlib.Path.home() / '.garf/cache/')
)
DEFAULT_CACHE_TTL: Final[int] = os.getenv('GARF_CACHE_TTL_SECONDS', 3600)


class GarfCache:
  """Stores and loads reports from a cache instead of calling API."""

  def __init__(
    self,
    location: str | None = None,
    ttl_seconds: int = DEFAULT_CACHE_TTL,
    cache_provider=None,
  ) -> None:
    """Initializes new cache.

    Args:
      location: Cache location.
      ttl_seconds: Maximum lifespan of cached objects.
      cache_provider: Instantiated cache provider.
    """
    self.location = location or DEFAULT_CACHE_LOCATION
    self.ttl_seconds = int(ttl_seconds)
    if cache_provider:
      self.cache_provider = cache_provider
    elif str(location).startswith('redis'):
      self.cache_provider = RedisGarfCache(self.location, self.ttl_seconds)
    else:
      self.cache_provider = FileGarfCache(self.location, self.ttl_seconds)

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
      hashlib.md5(
        json.dumps(kwargs).encode('utf-8'), usedforsecurity=False
      ).hexdigest()
      if kwargs
      else ''
    )
    hash_identifier = f'{query.hash}:{args_hash}:{kwargs_hash}'
    return self.cache_provider.load(hash_identifier, query)

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
    args_hash = args.hash if args else ''
    kwargs_hash = (
      hashlib.md5(
        json.dumps(kwargs).encode('utf-8'), usedforsecurity=False
      ).hexdigest()
      if kwargs
      else ''
    )
    hash_identifier = f'{query.hash}:{args_hash}:{kwargs_hash}'
    result = self.cache_provider.save(fetched_report, hash_identifier)
    logger.info('Report is saved to cache: %s', result)

  @property
  def size(self) -> int:
    return 0


class RedisGarfCache:
  """Stores and loads reports from Redis."""

  def __init__(
    self,
    location: str | None = None,
    ttl_seconds: int = DEFAULT_CACHE_TTL,
    redis_client: redis.Redis | None = None,
  ) -> None:
    self.location = location or DEFAULT_CACHE_LOCATION
    self.r = redis_client or redis.Redis.from_url(
      self.location, decode_responses=True
    )
    self.ttl_seconds = ttl_seconds

  def load(self, hash_identifier: str, query) -> report.GarfReport:
    """Loads report from cache based on query definition.

    Args:
      hash_identifier: Unique identifier of a query.

    Returns:
      Cached report.

    Raises:
      GarfCacheFileNotFoundError: If cached report not found
    """
    if not (data := self.r.get(hash_identifier)):
      raise GarfCacheFileNotFoundError
    logger.debug('Report is loaded from cache: %s', str(hash_identifier))
    loaded_report = report.GarfReport.from_json(data)
    loaded_report.query_specification = query
    return loaded_report

  def save(
    self,
    fetched_report: report.GarfReport,
    hash_identifier: str,
  ) -> None:
    """Saves report to cache based on query definition.

    Args:
      fetched_report: Report to save.
      hash_identifier: Unique identifier of a query.
    """
    data = json.dumps(fetched_report.to_list(row_type='dict'))
    self.r.set(hash_identifier, data, ex=self.ttl_seconds)
    logger.info('Report is saved to cache: %s', str(hash_identifier))
    return hash_identifier


class FileGarfCache:
  """Stores and loads reports from remote or local file storage.

  Attribute:
    location: Folder where cached results are stored.
  """

  def __init__(
    self,
    location: str | None = None,
    ttl_seconds: int = DEFAULT_CACHE_TTL,
  ) -> None:
    location = location or DEFAULT_CACHE_LOCATION
    if '://' in str(location):
      self.location = location
      self.type = 'remote'
    else:
      self.location = pathlib.Path(location)
      self.type = 'local'
    self.ttl_seconds = ttl_seconds

  @property
  def max_cache_timestamp(self) -> float:
    return (
      datetime.datetime.now() - datetime.timedelta(seconds=self.ttl_seconds)
    ).timestamp()

  def load(self, hash_identifier: str, query) -> report.GarfReport:
    """Loads report from cache based on query definition.

    Args:
      hash_identifier: Unique identifier of a query.

    Returns:
      Cached report.

    Raises:
      GarfCacheFileNotFoundError: If cached report not found
    """
    if self.type == 'local':
      cached_path = self.location / f'{hash_identifier}.json'
    else:
      cached_path = f'{self.location}/{hash_identifier}.json'
    if (
      self.type == 'local'
      and cached_path.exists()
      and cached_path.stat().st_ctime > self.max_cache_timestamp
    ):
      with smart_open.open(cached_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    elif self.type == 'remote':
      try:
        with smart_open.open(cached_path, 'r', encoding='utf-8') as f:
          data = json.load(f)
      except Exception as e:
        raise GarfCacheFileNotFoundError from e
    else:
      raise GarfCacheFileNotFoundError
    logger.debug('Report is loaded from cache: %s', str(cached_path))
    loaded_report = report.GarfReport.from_json(json.dumps(data))
    loaded_report.query_specification = query
    return loaded_report

  def save(
    self, fetched_report: report.GarfReport, hash_identifier: str
  ) -> None:
    """Saves report to cache based on query definition.

    Args:
      fetched_report: Report to save.
      hash_identifier: Unique identifier of a query.
    """
    if self.type == 'local':
      self.location.mkdir(parents=True, exist_ok=True)
    if self.type == 'local':
      cached_path = self.location / f'{hash_identifier}.json'
    else:
      cached_path = f'{self.location}/{hash_identifier}.json'
    with smart_open.open(str(cached_path), 'w', encoding='utf-8') as f:
      json.dump(fetched_report.to_list(row_type='dict'), f)
    logger.info('Report is saved to cache: %s', str(cached_path))
    return str(cached_path)

  @property
  def size(self) -> int:
    total_size = 0
    if self.type == 'remote':
      return total_size
    for dirpath, dirnames, filenames in os.walk(self.location):
      for f in filenames:
        file_path = os.path.join(dirpath, f)
        if not os.path.islink(file_path):
          total_size += os.path.getsize(file_path)
    return total_size

  def clean(self) -> None:
    """Removes all cached files."""
    if self.type == 'remote':
      return
    for item in self.location.iterdir():
      if item.is_dir():
        shutil.rmtree(item)
      else:
        item.unlink()

  def prune(self, ttl: int = 30) -> int:
    """Removes all files older that a lookback in days.

    Args:
      ttl: Max cache entry size in days.

    Returns:
      Number of bytes pruned.
    """
    pruned_file_size = 0
    if self.type == 'remote':
      return pruned_file_size
    prune_date = datetime.datetime.now(
      datetime.timezone.utc
    ) - datetime.timedelta(days=ttl)
    for file_path in self.location.rglob('*.json'):
      if (
        file_path.is_file()
        and datetime.datetime.fromtimestamp(
          file_path.stat().st_mtime, datetime.timezone.utc
        )
        < prune_date
      ):
        pruned_file_size += os.path.getsize(file_path)
        file_path.unlink()
    return pruned_file_size
