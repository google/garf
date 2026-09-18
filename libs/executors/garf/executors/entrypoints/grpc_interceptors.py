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
import os

import grpc
import jwt


class JWTAuthInterceptor(grpc.ServerInterceptor):
  def __init__(
    self,
    public_key: str,
    expected_audience: str = os.getenv('JWT_AUDIENCE', 'garf-service'),
    expected_issuer: str = os.getenv('JWT_ISSUER', 'urn:garf:local:issuer'),
    algorithms: list[str] | None = None,
  ):
    self._public_key = public_key
    self._expected_audience = expected_audience
    self._expected_issuer = expected_issuer
    self._algorithms = algorithms or ['RS256']

  def intercept_service(self, continuation, handler_call_details):
    metadata = dict(handler_call_details.invocation_metadata or ())
    auth_header = metadata.get('authorization', '')

    if not auth_header.startswith('Bearer '):
      return self._abort_handler(
        continuation(handler_call_details),
        "Missing or malformed Authorization header (expected 'Bearer <token>')",
      )

    token = auth_header.split(' ', 1)[1].strip()

    try:
      jwt.decode(
        token,
        self._public_key,
        algorithms=self._algorithms,
        audience=self._expected_audience,
        issuer=self._expected_issuer,
        options={'require': ['exp', 'iss', 'aud']},
      )
    except jwt.ExpiredSignatureError:
      return self._abort_handler(
        continuation(handler_call_details), 'JWT has expired'
      )
    except jwt.InvalidTokenError as e:
      return self._abort_handler(
        continuation(handler_call_details), f'Invalid JWT: {str(e)}'
      )

    return continuation(handler_call_details)

  def _abort_handler(self, handler, message: str):
    if handler is None:
      return None

    def abort_call(ignored_request, context):
      context.abort(grpc.StatusCode.UNAUTHENTICATED, message)

    if handler.unary_unary:
      return grpc.unary_unary_rpc_method_handler(
        abort_call,
        request_deserializer=handler.request_deserializer,
        response_serializer=handler.response_serializer,
      )
    if handler.unary_stream:
      return grpc.unary_stream_rpc_method_handler(
        abort_call,
        request_deserializer=handler.request_deserializer,
        response_serializer=handler.response_serializer,
      )
    if handler.stream_unary:
      return grpc.stream_unary_rpc_method_handler(
        abort_call,
        request_deserializer=handler.request_deserializer,
        response_serializer=handler.response_serializer,
      )
    if handler.stream_stream:
      return grpc.stream_stream_rpc_method_handler(
        abort_call,
        request_deserializer=handler.request_deserializer,
        response_serializer=handler.response_serializer,
      )
    return handler


class TokenAuthInterceptor(grpc.ServerInterceptor):
  def __init__(self, expected_token: str, header_key: str = 'authorization'):
    self._expected_token = expected_token
    self._header_key = header_key

  def intercept_service(self, continuation, handler_call_details):
    metadata = dict(handler_call_details.invocation_metadata)
    auth_header = metadata.get(self._header_key)

    if auth_header != f'Bearer {self._expected_token}':

      def abort(ignored_request, context):
        context.abort(
          grpc.StatusCode.UNAUTHENTICATED,
          'Invalid or missing authentication token',
        )

      return grpc.unary_unary_rpc_method_handler(abort)

    return continuation(handler_call_details)
