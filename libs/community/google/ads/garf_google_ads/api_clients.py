# Copyright 2025 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the 'License');
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an 'AS IS' BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Creates API client for Google Ads API."""

from __future__ import annotations

import importlib
import logging
import os
from pathlib import Path
from typing import Final

import google.auth
import smart_open
import tenacity
import yaml
from garf_core import api_clients
from google.ads.googleads import client as googleads_client
from google.api_core import exceptions as google_exceptions
from typing_extensions import override

from garf_google_ads import exceptions, query_editor

GOOGLE_ADS_API_VERSION: Final = googleads_client._DEFAULT_VERSION
google_ads_service = importlib.import_module(
  f'google.ads.googleads.{GOOGLE_ADS_API_VERSION}.'
  'services.types.google_ads_service'
)


class GoogleAdsApiClientError(exceptions.GoogleAdsApiError):
  """Google Ads API client specific error."""


class GoogleAdsApiClient(api_clients.BaseClient):
  """Client to interact with Google Ads API.

  Attributes:
    default_google_ads_yaml: Default location for google-ads.yaml file.
    client: GoogleAdsClient to perform stream and mutate operations.
    ads_service: GoogleAdsService to perform stream operations.
  """

  default_google_ads_yaml = str(Path.home() / 'google-ads.yaml')

  def __init__(
    self,
    path_to_config: str | os.PathLike[str] = os.getenv(
      'GOOGLE_ADS_CONFIGURATION_FILE_PATH', default_google_ads_yaml
    ),
    config_dict: dict[str, str] | None = None,
    yaml_str: str | None = None,
    version: str = GOOGLE_ADS_API_VERSION,
    use_proto_plus: bool = True,
    ads_client: googleads_client.GoogleAdsClient | None = None,
    **kwargs: str,
  ) -> None:
    """Initializes GoogleAdsApiClient based on one of the methods.

    Args:
      path_to_config: Path to google-ads.yaml file.
      config_dict: A dictionary containing authentication details.
      yaml_str: Strings representation of google-ads.yaml.
      version: Ads API version.
      use_proto_plus: Whether to convert Enums to names in response.
      ads_client: Instantiated GoogleAdsClient.

    Raises:
      GoogleAdsApiClientError:
         When GoogleAdsClient cannot be instantiated due to missing
         credentials.
    """
    self.api_version = version
    self.client = ads_client or self._init_client(
      path=path_to_config, config_dict=config_dict, yaml_str=yaml_str
    )
    self.client.use_proto_plus = use_proto_plus
    self.ads_service = self.client.get_service('GoogleAdsService')
    self.kwargs = kwargs

  @override
  @tenacity.retry(
    stop=tenacity.stop_after_attempt(3),
    wait=tenacity.wait_exponential(),
    retry=tenacity.retry_if_exception_type(
      google_exceptions.InternalServerError
    ),
    reraise=True,
  )
  def get_response(
    self, request: query_editor.GoogleAdsApiQuery, account: int, **kwargs: str
  ) -> api_clients.GarfApiResponse:
    """Executes query for a given entity_id (customer_id).

    Args:
        account: Google Ads customer_id.
        query_text: GAQL query text.

    Returns:
        SearchGoogleAdsStreamResponse for a given API version.

    Raises:
        google_exceptions.InternalServerError:
            When data cannot be fetched from Ads API.
    """
    response = self.ads_service.search_stream(
      customer_id=account, query=request.text
    )
    results = [result for batch in response for result in batch.results]
    return api_clients.GarfApiResponse(results=results)

  def _init_client(
    self,
    path: str | None = None,
    config_dict: dict[str, str] | None = None,
    yaml_str: str | None = None,
  ) -> googleads_client.GoogleAdsClient | None:
    """Initializes GoogleAdsClient based on one of the methods.

    Args:
      path: Path to google-ads.yaml file.
      config_dict: A dictionary containing authentication details.
      yaml_str: Strings representation of google-ads.yaml.

    Returns:
      Instantiated GoogleAdsClient;
      None if instantiation hasn't been done.

    Raises:
      GoogleAdsApiClientError:
        if google-ads.yaml wasn't found or missing crucial parts.
    """
    if config_dict:
      if not (developer_token := config_dict.get('developer_token')):
        raise GoogleAdsApiClientError('developer_token is missing.')
      if (
        'refresh_token' not in config_dict
        and 'json_key_file_path' not in config_dict
      ):
        credentials, _ = google.auth.default(
          scopes=['https://www.googleapis.com/auth/adwords']
        )
        if login_customer_id := config_dict.get('login_customer_id'):
          login_customer_id = str(login_customer_id)

        return googleads_client.GoogleAdsClient(
          credentials=credentials,
          developer_token=developer_token,
          login_customer_id=login_customer_id,
        )
      return googleads_client.GoogleAdsClient.load_from_dict(
        config_dict, self.api_version
      )
    if yaml_str:
      return googleads_client.GoogleAdsClient.load_from_string(
        yaml_str, self.api_version
      )
    if path:
      with smart_open.open(path, 'r', encoding='utf-8') as f:
        google_ads_config_dict = yaml.safe_load(f)
      return self._init_client(config_dict=google_ads_config_dict)
    try:
      return googleads_client.GoogleAdsClient.load_from_env(self.api_version)
    except ValueError as e:
      raise GoogleAdsApiClientError(
        f'Cannot instantiate GoogleAdsClient: {str(e)}'
      ) from e

  @classmethod
  def from_googleads_client(
    cls,
    ads_client: googleads_client.GoogleAdsClient,
    use_proto_plus: bool = True,
  ) -> GoogleAdsApiClient:
    """Builds GoogleAdsApiClient from instantiated GoogleAdsClient.

    ads_client: Instantiated GoogleAdsClient.
    use_proto_plus: Whether to convert Enums to names in response.

    Returns:
      Instantiated GoogleAdsApiClient.
    """
    if use_proto_plus != ads_client.use_proto_plus:
      logging.warning(
        'Mismatch between values of "use_proto_plus" in '
        'GoogleAdsClient and GoogleAdsApiClient, setting '
        f'"use_proto_plus={use_proto_plus}"'
      )
    return cls(
      ads_client=ads_client,
      version=ads_client.version,
      use_proto_plus=use_proto_plus,
    )
