# Copyright 2024 Google LLC
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

"""Defines simplified imports."""

from __future__ import annotations

from garf_knowledge_graph_api.api_clients import KnowledgeGraphApiClient
from garf_knowledge_graph_api.report_fetcher import (
  KnowledgeGraphApiReportFetcher,
)

__all__ = [
  'KnowledgeGraphApiClient',
  'KnowledgeGraphApiReportFetcher',
]

__version__ = '0.0.1'
