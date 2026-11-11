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
"""`garf-core` contains the base abstractions for garf framework.

These abstractions are used by an implementation for a concrete reporting API.
"""

import structlog
from garf.core.base_query import BaseQuery
from garf.core.report import GarfReport
from garf.core.report_fetcher import ApiReportFetcher

if not structlog.is_configured():
  structlog.configure(
    processors=[
      structlog.contextvars.merge_contextvars,
      structlog.stdlib.add_logger_name,
      structlog.stdlib.add_log_level,
      structlog.stdlib.PositionalArgumentsFormatter(),
      structlog.processors.StackInfoRenderer(),
      structlog.processors.format_exc_info,
      structlog.processors.UnicodeDecoder(),
      structlog.dev.ConsoleRenderer(colors=False),
    ],
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=False,
  )

__all__ = [
  'BaseQuery',
  'GarfReport',
  'ApiReportFetcher',
]
