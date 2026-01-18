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
"""A client and common configurations for the Search Ads 360 API."""

import json
import os
from dataclasses import dataclass
from typing import AnyStr, Optional, Sequence, Tuple

import pkg_resources
import yaml

try:
  import grpc.experimental
  from google.ads.searchads360.v0.services.services.customer_service import (
    client as customer_service_client,
  )
  from google.ads.searchads360.v0.services.services.search_ads360_service import (
    client as search_ads360_service_client,
  )
  from google.ads.searchads360.v0.services.types import (
    search_ads360_service as types,
  )
  from google.oauth2.credentials import Credentials as InstalledAppCredentials
  from google.protobuf.internal import api_implementation
  from grpc import (
    CallCredentials,
    ClientCallDetails,
    UnaryStreamClientInterceptor,
    UnaryUnaryClientInterceptor,
  )
except ImportError as e:
  raise ImportError(
    'Please install garf-google-ads with Search Ads 360 support - '
    '`pip install garf-google-ads[search-ads-360]`'
  ) from e

_DEFAULT_LOGIN_CUSTOMER_ID = '0'
_REQUEST_ID_KEY = 'request-id'
_REQUEST_ID_KEY = 'request-id'


# See options at grpc.github.io/grpc/core/group__grpc__arg__keys.html
_GRPC_CHANNEL_OPTIONS = [
  ('grpc.max_metadata_size', 16 * 1024 * 1024),
  ('grpc.max_receive_message_length', 64 * 1024 * 1024),
]


class _Interceptor:
  """An interceptor base class."""

  _SENSITIVE_INFO_MASK = 'REDACTED'

  @dataclass
  class _ClientCallDetails(ClientCallDetails):
    """Wrapper class for initializing a new ClientCallDetails instance."""

    method: str
    timeout: Optional[float]
    metadata: Optional[Sequence[Tuple[str, AnyStr]]]
    credentials: Optional[CallCredentials]

  @classmethod
  def get_request_id_from_metadata(cls, trailing_metadata):
    """Gets the request ID for the Search Ads 360 API request.

    Args:
      trailing_metadata: a tuple of metadatum from the service response.

    Returns:
      A str request ID associated with the Search Ads 360 API request, or
      None
      if it doesn't exist.
    """
    for kv in trailing_metadata:
      if kv[0] == _REQUEST_ID_KEY:
        return kv[1]  # Return the found request ID.

    return None

  @classmethod
  def parse_metadata_to_json(cls, metadata):
    """Parses metadata from gRPC request and response messages to a JSON str.

    Args:
      metadata: a tuple of metadatum.

    Returns:
      A str of metadata formatted as JSON key/value pairs.
    """
    metadata_dict = {}

    if metadata is None:
      return '{}'

    for datum in metadata:
      key = datum[0]
      value = datum[1]
      metadata_dict[key] = value

    return cls.format_json_object(metadata_dict)

  @classmethod
  def format_json_object(cls, obj):
    """Parses a serializable object into a consistently formatted JSON string.

    Returns:
      A str of formatted JSON serialized from the given object.

    Args:
      obj: an object or dict.
    """

    def default_serializer(value):
      if isinstance(value, bytes):
        return value.decode(errors='ignore')
      return None

    return str(
      json.dumps(
        obj,
        indent=2,
        sort_keys=True,
        ensure_ascii=False,
        default=default_serializer,
        separators=(',', ': '),
      )
    )

  @classmethod
  def get_trailing_metadata_from_interceptor_exception(cls, exception):
    """Retrieves trailing metadata from an exception object.

    Args:
      exception: an instance of grpc.Call.

    Returns:
      A tuple of trailing metadata key value pairs.
    """
    try:
      # SearchAds360Failure exceptions will contain trailing metadata on the
      # error attribute.
      return exception.error.trailing_metadata()
    except AttributeError:
      try:
        # Transport failures, i.e. issues at the gRPC layer, will contain
        # trailing metadata on the exception itself.
        return exception.trailing_metadata()
      except AttributeError:
        # if trailing metadata is not found in either location then
        # return an empty tuple
        return tuple()

  @classmethod
  def get_client_call_details_instance(
    cls, method, timeout, metadata, credentials=None
  ):
    """Initializes an instance of the ClientCallDetails with the given data.

    Args:
      method: A str of the service method being invoked.
      timeout: A float of the request timeout
      metadata: A list of metadata tuples
      credentials: An optional grpc.CallCredentials instance for the RPC

    Returns:
      An instance of _ClientCallDetails that wraps grpc.ClientCallDetails.
    """
    return cls._ClientCallDetails(method, timeout, metadata, credentials)


try:
  _PROTOBUF_VERSION = pkg_resources.get_distribution('protobuf').version
except pkg_resources.DistributionNotFound:
  # If the distribution can't be found for whatever reason then we set
  # the version to None so that we can know to leave this header out of the
  # request.
  _PROTOBUF_VERSION = None

# Determine which protobuf implementation is being used.
if api_implementation.Type() == 'cpp':
  _PB_IMPL_HEADER = '+c'
elif api_implementation.Type() == 'python':
  _PB_IMPL_HEADER = '+n'
else:
  _PB_IMPL_HEADER = ''


class _MetadataInterceptor(
  _Interceptor, UnaryUnaryClientInterceptor, UnaryStreamClientInterceptor
):
  """An interceptor that appends custom metadata to requests."""

  def __init__(self, login_customer_id):
    """Initialization method for this class.

    Args:
      login_customer_id: a str specifying a login customer ID.
    """
    self.login_customer_id_meta = (
      ('login-customer-id', login_customer_id) if login_customer_id else None
    )

  def _update_client_call_details_metadata(self, client_call_details, metadata):
    """Updates the client call details with additional metadata.

    Args:
      client_call_details: An instance of grpc.ClientCallDetails.
      metadata: Additional metadata defined by SearchAds360Client.

    Returns:
      A new instance of grpc.ClientCallDetails with additional metadata
      from the SearchAds360Client.
    """
    client_call_details = self.get_client_call_details_instance(
      client_call_details.method,
      client_call_details.timeout,
      metadata,
      client_call_details.credentials,
    )

    return client_call_details

  def _intercept(self, continuation, client_call_details, request):
    """Generic interceptor used for Unary-Unary and Unary-Stream requests.

    Args:
      continuation: a function to continue the request process.
      client_call_details: a grpc._interceptor._ClientCallDetails instance
        containing request metadata.
      request: a SearchSearchAds360Request or
        SearchSearchAds360RequestStreamRequest message class instance.

    Returns:
      A grpc.Call/grpc.Future instance representing a service response.
    """
    if client_call_details.metadata is None:
      metadata = []
    else:
      metadata = list(client_call_details.metadata)

    if self.login_customer_id_meta:
      metadata.append(self.login_customer_id_meta)

    for i, metadatum in enumerate(metadata):
      # Check if the user agent header key is in the current metadatum
      if 'x-goog-api-client' in metadatum and _PROTOBUF_VERSION:
        # Convert the tuple to a list so it can be modified.
        metadatum = list(metadatum)
        # Check that "pb" isn't already included in the user agent.
        if 'pb' not in metadatum[1]:
          # Append the protobuf version key value pair to the end of
          # the string.
          metadatum[1] += f' pb/{_PROTOBUF_VERSION}{_PB_IMPL_HEADER}'
          # Convert the metadatum back to a tuple.
          metadatum = tuple(metadatum)
          # Splice the metadatum back in its original position in
          # order to preserve the order of the metadata list.
          metadata[i] = metadatum
          # Exit the loop since we already found the user agent.
          break

    client_call_details = self._update_client_call_details_metadata(
      client_call_details, metadata
    )

    return continuation(client_call_details, request)

  def intercept_unary_unary(self, continuation, client_call_details, request):
    """Intercepts and appends custom metadata for Unary-Unary requests.

    Overrides abstract method defined in grpc.UnaryUnaryClientInterceptor.

    Args:
      continuation: a function to continue the request process.
      client_call_details: a grpc._interceptor._ClientCallDetails instance
        containing request metadata.
      request: a SearchSearchAds360Request or SearchSearchAds360StreamRequest
        message class instance.

    Returns:
      A grpc.Call/grpc.Future instance representing a service response.
    """
    return self._intercept(continuation, client_call_details, request)

  def intercept_unary_stream(self, continuation, client_call_details, request):
    """Intercepts and appends custom metadata to Unary-Stream requests.

    Overrides abstract method defined in grpc.UnaryStreamClientInterceptor.

    Args:
      continuation: a function to continue the request process.
      client_call_details: a grpc._interceptor._ClientCallDetails instance
        containing request metadata.
      request: a SearchSearchAds360Request or SearchSearchAds360StreamRequest
        message class instance.

    Returns:
      A grpc.Call/grpc.Future instance representing a service response.
    """
    return self._intercept(continuation, client_call_details, request)


class SearchAds360Client:
  """Search Ads 360 client used to configure settings and fetch services."""

  def __init__(self, credentials, refresh_token, login_customer_id):
    """Initializer for the SearchAds360Client.

    Args:
      credentials: a google.oauth2.credentials.Credentials instance.
      refresh_token: a str refresh token.
      login_customer_id: a str specifying a login customer ID.
    """
    self.credentials = credentials
    self.refresh_token = refresh_token
    self.login_customer_id = login_customer_id

  def _set_ids(self, customer_id, login_customer_id):
    """Overrides login_customer_id field with value specified in parameter.

    Determine login_customer_id from multiple income sources. customer_id will
    be used as login_customer_id if login_customer_id is null.

    Args:
      customer_id: a str specifying a login customer ID.
      login_customer_id: a str specifying a login customer ID, can be null.
    """
    if login_customer_id:
      self.login_customer_id = login_customer_id
    elif self.login_customer_id == 'None':
      self.login_customer_id = customer_id

  @classmethod
  def load_from_file(cls, yaml_str=None):
    """Creates a SearchAds360Client with data stored in the YAML string.

    Args:
      yaml_str: a str containing YAML configuration data used to initialize a
        SearchAds360Client.

    Returns:
      A SearchAds360Client initialized with the values specified in the
      string.

    Raises:
      ValueError: If the configuration lacks a required field.
    """
    config_data = _load_from_yaml_file(yaml_str)
    kwargs = cls._get_client_kwargs(config_data)
    return cls(**dict(**kwargs))

  @classmethod
  def _get_client_kwargs(cls, config_data):
    """Converts configuration dict into kwargs required by the client.

    Args:
      config_data: a dict containing client configuration.

    Returns:
      A dict containing kwargs that will be provided to the
      SearchAds360Client initializer.

    Raises:
      ValueError: If the configuration lacks a required field.
    """
    client_id = config_data.get('client_id')
    client_secret = config_data.get('client_secret')
    refresh_token = config_data.get('refresh_token')
    login_customer_id = str(config_data.get('login_customer_id'))

    return {
      'credentials': cls._get_credentials(
        cls, client_id, client_secret, refresh_token
      ),
      'refresh_token': refresh_token,
      'login_customer_id': login_customer_id,
    }

  def _get_credentials(self, client_id, client_secret, refresh_token):
    return InstalledAppCredentials(
      None,
      client_id=client_id,
      client_secret=client_secret,
      refresh_token=refresh_token,
      token_uri='https://accounts.google.com/o/oauth2/token',
    )

  def get_service(self):
    """Returns a SearchAds360 service client instance.

    Returns:
      A service client instance.
    """
    service_transport_class = search_ads360_service_client.SearchAds360ServiceClient.get_transport_class(  # pylint: disable=line-too-long
    )

    endpoint = (
      search_ads360_service_client.SearchAds360ServiceClient.DEFAULT_ENDPOINT
    )
    channel = service_transport_class.create_channel(
      host=endpoint,
      credentials=self.credentials,
      options=_GRPC_CHANNEL_OPTIONS,
    )

    interceptors = [
      _MetadataInterceptor(
        self.login_customer_id,
      ),
    ]

    channel = grpc.intercept_channel(channel, *interceptors)

    service_transport = service_transport_class(channel=channel)

    return search_ads360_service_client.SearchAds360ServiceClient(
      transport=service_transport
    )

  def _get_customer_service(self):
    """Returns a customer service client instance.

    Returns:
      A customer service client instance.
    """
    service_transport_class = (
      customer_service_client.CustomerServiceClient.get_transport_class()
    )

    endpoint = customer_service_client.CustomerServiceClient.DEFAULT_ENDPOINT
    channel = service_transport_class.create_channel(
      host=endpoint,
      credentials=self.credentials,
      options=[],
    )

    if self.login_customer_id == 'None':
      self.login_customer_id = _DEFAULT_LOGIN_CUSTOMER_ID

    interceptors = [
      _MetadataInterceptor(
        self.login_customer_id,
      ),
    ]

    channel = grpc.intercept_channel(channel, *interceptors)

    service_transport = service_transport_class(channel=channel)

    return customer_service_client.CustomerServiceClient(
      transport=service_transport
    )


def _load_from_yaml_file(path=None):
  """Loads configuration data from a YAML file and returns it as a dict.

  Args:
    path: a str indicating the path to a YAML file containing configuration data
      used to initialize a SearchAds360Client.

  Returns:
    A dict with configuration from the specified YAML file.

  Raises:
    FileNotFoundError: If the specified configuration file doesn't exist.
    IOError: If the configuration file can't be loaded.
  """
  if path is None:
    path = os.path.join(os.path.expanduser('~'), 'search-ads-360.yaml')

  if not os.path.isabs(path):
    path = os.path.expanduser(path)
  with open(path, 'rb') as handle:
    yaml_doc = handle.read()

  return yaml.safe_load(yaml_doc) or {}


SearchAds360Row = types.SearchAds360Row
SearchSearchAds360StreamRequest = types.SearchSearchAds360StreamRequest
