# Copyright 2024 Google LLC
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
import os

from garf_io import writer
from garf_youtube_data_api import api_clients, report_fetcher

query = 'SELECT id, snippet.title AS channel_name FROM channels'
api_client = api_clients.YouTubeDataApiClient(
  api_key=os.getenv('YOUTUBE_DATA_API_KEY')
)
fetched_report = report_fetcher.YouTubeDataApiReportFetcher(
  api_client=api_client
).fetch(query, id=['UC1oXUA7qgs0GZc_yk46K2OQ'])

json_writer = writer.create_writer('console')
json_writer.write(fetched_report, 'output')
