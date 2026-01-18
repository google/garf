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
import re
from pathlib import Path
from types import ModuleType
from typing import Any, Final

import google.auth
import proto
import pydantic
import smart_open
import tenacity
import yaml
from garf.community.google.ads import exceptions, query_editor
from garf.core import api_clients
from google import protobuf
from google.ads.googleads import client as googleads_client
from google.api_core import exceptions as google_exceptions
from typing_extensions import override

GOOGLE_ADS_API_VERSION: Final = googleads_client._DEFAULT_VERSION
google_ads_service = importlib.import_module(
  f'google.ads.googleads.{GOOGLE_ADS_API_VERSION}.'
  'services.types.google_ads_service'
)


class FieldPossibleValues(pydantic.BaseModel):
  name: str
  values: set[Any]


class GoogleAdsApiClientError(exceptions.GoogleAdsApiError):
  """Google Ads API client specific error."""


class SearchAds360ApiClient(api_clients.BaseClient):
  """Client to interact Search Ads 360 API.

  Attributes:
    default_config: Default location for search-ads-360.yaml file.
    client: GoogleAdsClient to perform stream and mutate operations.
    search_ads_360_service: Service to perform stream operations.
  """

  default_config = str(Path.home() / 'search-ads-360.yaml')

  def __init__(
    self,
    path_to_config: str | os.PathLike[str] = os.getenv(
      'SEARCH_ADS_360_CONFIGURATION_FILE_PATH', default_config
    ),
    **kwargs: str,
  ) -> None:
    """Initializes SearchAds360ApiClient based on a config file.

    Args:
      path_to_config: Path to search-ads-360.yaml file.
    """
    from garf.community.google.ads import search_ads_360_client

    self.client = search_ads_360_client.SearchAds360Client.load_from_file(
      path_to_config
    )
    self.search_ads_360_service = self.client.get_service()
    self.kwargs = kwargs

  def get_response(
    self, request, account: int, **kwargs: str
  ) -> api_clients.GarfApiResponse:
    from garf.community.google.ads import search_ads_360_client

    request = search_ads_360_client.SearchSearchAds360StreamRequest(
      query=request.text, customer_id=account
    )
    response = self.search_ads_360_service.search_stream(request)
    results = [result for batch in response for result in batch.results]
    return api_clients.GarfApiResponse(
      results=results,
      results_placeholder=[search_ads_360_client.SearchAds360Row()],
    )


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
    self.api_version = (
      str(version) if str(version).startswith('v') else f'v{version}'
    )
    self.client = ads_client or self._init_client(
      path=path_to_config, config_dict=config_dict, yaml_str=yaml_str
    )
    self.client.use_proto_plus = use_proto_plus
    self.ads_service = self.client.get_service('GoogleAdsService')
    self.kwargs = kwargs

  @property
  def _base_module(self) -> str:
    """Name of Google Ads module for a given API version."""
    return f'google.ads.googleads.{self.api_version}'

  @property
  def _common_types_module(self) -> str:
    """Name of module containing common data types."""
    return f'{self._base_module}.common.types'

  @property
  def _metrics(self) -> ModuleType:
    """Module containing metrics."""
    return importlib.import_module(f'{self._common_types_module}.metrics')

  @property
  def _segments(self) -> ModuleType:
    """Module containing segments."""
    return importlib.import_module(f'{self._common_types_module}.segments')

  def _get_google_ads_row(self) -> google_ads_service.GoogleAdsRow:
    """Gets GoogleAdsRow proto message for a given API version."""
    google_ads_service = importlib.import_module(
      f'google.ads.googleads.{self.api_version}.'
      f'services.types.google_ads_service'
    )
    return google_ads_service.GoogleAdsRow()

  def get_types(self, request):
    return []

  def _get_types(self, request):
    output = []
    for field_name in request.fields:
      try:
        descriptor = self._get_descriptor(field_name)
        values = self._get_possible_values_for_resource(descriptor)
        field = FieldPossibleValues(name=field_name, values=values)
      except (AttributeError, ModuleNotFoundError):
        field = FieldPossibleValues(
          name=field_name,
          values={
            '',
          },
        )
      output.append(field)
    return output

  def _get_descriptor(
    self, field: str
  ) -> protobuf.descriptor_pb2.FieldDescriptorProto:
    """Gets descriptor for specified field.

    Args:
        field: Valid field name to be sent to Ads API.

    Returns:
        FieldDescriptorProto for specified field.
    """
    resource, *sub_resource, base_field = field.split('.')
    base_field = 'type_' if base_field == 'type' else base_field
    target_resource = self._get_target_resource(resource, sub_resource)
    return target_resource.meta.fields.get(base_field).descriptor

  def _get_target_resource(
    self, resource: str, sub_resource: list[str] | None = None
  ) -> proto.message.Message:
    """Gets Proto message for specified resource and its sub-resources.

    Args:
        resource:
            Google Ads resource (campaign, ad_group, segments, etc.).
        sub_resource:
            Possible sub-resources (date for segments resource).

    Returns:
        Proto describing combination of resource and sub-resource.
    """
    if resource == 'metrics':
      target_resource = self._metrics.Metrics
    elif resource == 'segments':
      # If segment has name segments.something.something
      if sub_resource:
        target_resource = getattr(
          self._segments, f'{clean_resource(sub_resource[-1])}'
        )
      else:
        target_resource = getattr(self._segments, f'{clean_resource(resource)}')
    else:
      resource_module = importlib.import_module(
        f'{self._base_module}.resources.types.{resource}'
      )

      target_resource = getattr(resource_module, f'{clean_resource(resource)}')
      try:
        # If resource has name resource.something.something
        if sub_resource:
          target_resource = getattr(
            target_resource, f'{clean_resource(sub_resource[-1])}'
          )
      except AttributeError:
        try:
          resource_module = importlib.import_module(
            f'{self._base_module}.resources.types.{sub_resource[0]}'
          )
        except ModuleNotFoundError:
          resource_module = importlib.import_module(
            f'{self._common_types_module}.{sub_resource[0]}'
          )
        if len(sub_resource) > 1:
          if hasattr(resource_module, f'{clean_resource(sub_resource[1])}'):
            target_resource = getattr(
              resource_module, f'{clean_resource(sub_resource[-1])}'
            )
          else:
            resource_module = importlib.import_module(
              f'{self._common_types_module}.ad_type_infos'
            )

            target_resource = getattr(
              resource_module, f'{clean_resource(sub_resource[1])}Info'
            )
        else:
          target_resource = getattr(
            resource_module, f'{clean_resource(sub_resource[-1])}'
          )
    return target_resource

  def _get_possible_values_for_resource(
    self, descriptor: protobuf.descriptor_pb2.FieldDescriptorProto
  ) -> set:
    """Identifies possible values for a given descriptor or field_type.

    If descriptor's type is ENUM function gets all possible values for
    this Enum, otherwise the default value for descriptor type is taken
    (0 for int, '' for str, False for bool).

    Args:
        descriptor: FieldDescriptorProto for specified field.

    Returns:
        Possible values for a given descriptor.
    """
    mapping = {
      'INT64': int,
      'FLOAT': float,
      'DOUBLE': float,
      'BOOL': bool,
    }
    if descriptor.type == 14:  # 14 stands for ENUM
      enum_class, enum = descriptor.type_name.split('.')[-2:]
      file_name = re.sub(r'(?<!^)(?=[A-Z])', '_', enum).lower()
      enum_resource = importlib.import_module(
        f'{self._base_module}.enums.types.{file_name}'
      )
      return {p.name for p in getattr(getattr(enum_resource, enum_class), enum)}

    field_type = mapping.get(
      proto.primitives.ProtoType(descriptor.type).name, str
    )
    default_value = field_type()
    return {
      default_value,
    }

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
    """Executes a single API request for a given customer_id and GAQL query."""
    response = self.ads_service.search_stream(
      customer_id=account, query=request.text
    )
    results = [result for batch in response for result in batch.results]
    return api_clients.GarfApiResponse(
      results=results, results_placeholder=[self._get_google_ads_row()]
    )

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


def clean_resource(resource: str) -> str:
  """Converts nested resource to a TitleCase format."""
  return resource.title().replace('_', '')
