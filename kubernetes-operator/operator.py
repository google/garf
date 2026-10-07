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
from typing import Any, Final

import kopf
import kubernetes
import pydantic

GARF_CLI_IMAGE: Final[str] = os.getenv(
  'GARF_CLI_IMAGE', 'ghcr.io/google/garf-go:latest'
)


class ServerInfo(pydantic.BaseModel):
  url: str | None = None
  server_type: str = None

  def __bool__(self) -> bool:
    return bool(self.url and self.server_type)


class GarfCronJob(pydantic.BaseModel):
  context: dict[str, Any] = pydantic.Field(default_factory=dict)
  config_path: str | None = None
  server_info: ServerInfo | None = None
  env: list[dict[str, Any]] = pydantic.Field(default_factory=list)

  @property
  def command(self) -> list[str]:
    raise NotImplementedError

  @property
  def job_template(
    self,
  ) -> kubernetes.client.models.v1_job_template_spec.V1JobTemplateSpec:
    return kubernetes.client.models.v1_job_template_spec.V1JobTemplateSpec(
      spec={
        'template': {
          'spec': {
            'containers': [
              {
                'name': 'grf',
                'image': GARF_CLI_IMAGE,
                'args': self.command,
              }
            ],
            'restartPolicy': 'OnFailure',
          }
        }
      }
    )


class Query(pydantic.BaseModel):
  title: str
  text: str


class QueryPath(pydantic.BaseModel):
  path: str


class GarfQueryCronJob(GarfCronJob):
  queries: list[Query | QueryPath]
  source: str
  writer: str

  @property
  def command(self) -> list[str]:
    cli_args = [
      'execute',
      ' '.join(q.path for q in self.queries),
      f' --source {self.source} --writer {self.writer} --as-file ',
    ]

    if server := self.server_info:
      cli_args.append(f'--endpoint={server.url}')

    if self.config_path:
      cli_args.append(f'--config {self.config_path}')
    return ' '.join(cli_args).split(' ')


class GarfWorkflowCronJob(GarfCronJob):
  workflow_path: str

  @property
  def command(self) -> list[str]:
    cli_args = ['workflow run', f'-f {self.workflow_path} --as-file ']

    if server := self.server_info:
      cli_args.append(f'--endpoint={server.url}')

    if self.config_path:
      cli_args.append(f'--config {self.config_path}')
    return ' '.join(cli_args).split(' ')


def _build_cron_job(
  name: str, namespace: str | None, spec: kopf.Spec, cronjob_type: str
) -> kubernetes.client.V1CronJob:
  if cronjob_type == 'GarfWorkflowCronJob':
    cronjob = GarfWorkflowCronJob(
      workflow_path=spec.get('workflowPath'),
      config_path=spec.get('configPath'),
      server_info=spec.get('server'),
      env=spec.get('env'),
    )
  elif cronjob_type == 'GarfQueryCronJob':
    cronjob = GarfQueryCronJob(
      queries=spec.get('queries'),
      source=spec.get('source'),
      writer=spec.get('writer'),
      config_path=spec.get('configPath'),
      context=spec.get('context'),
      server_info=spec.get('server'),
      env=spec.get('env'),
    )
  else:
    raise kopf.PermanentError(f'Failed to delete GarfCronJob: {e}')
  return kubernetes.client.V1CronJob(
    api_version='batch/v1',
    kind='CronJob',
    metadata={
      'name': name,
      'namespace': namespace,
    },
    spec={
      'schedule': spec.get('schedule'),
      'jobTemplate': cronjob.job_template,
    },
  )


@kopf.on.create('garf.io', 'v1', 'garfworkflowcronjobs')
def create_workflow_cj(
  body: kopf.Body,
  spec: kopf.Spec,
  name: str,
  namespace: str | None,
  logger: kopf.Logger,
  **kwargs,
) -> None:
  cronjob = _build_cron_job(
    name=name, namespace=namespace, spec=spec, cronjob_type=body['kind']
  )
  batch_v1 = kubernetes.client.BatchV1Api()
  try:
    batch_v1.create_namespaced_cron_job(namespace=namespace, body=cronjob)
    logger.info(f'Successfully created GarfWorkflowCronJob: {namespace}/{name}')
  except kubernetes.client.exceptions.ApiException as e:
    if e.status == 409:
      batch_v1.patch_namespaced_cron_job_status(
        name=name, namespace=namespace, body=cronjob
      )
      logger.info(f'GarfWorkflowCronJob exists, patching: {namespace}/{name}')
    else:
      raise kopf.PermanentError(f'Failed to create GarfWorkflowCronJob: {e}')


@kopf.on.delete('garf.io', 'v1', 'garfworkflowcronjobs')
def delete_workflow_cj(
  name: str, namespace: str | None, logger: kopf.Logger, **kwargs
) -> None:
  batch_v1 = kubernetes.client.BatchV1Api()
  try:
    batch_v1.delete_namespaced_cron_job(name=name, namespace=namespace)
    logger.info(f'Successfully deleted GarfWorkflowCronJob: {namespace}/{name}')
  except kubernetes.client.exceptions.ApiException as e:
    if e.status == 404:
      logger.info(
        f'GarfWorkflowCronJob {name} already deleted or does not exist'
      )
    else:
      raise kopf.PermanentError(f'Failed to delete GarfWorkflowCronJob: {e}')


@kopf.on.create('garf.io', 'v1', 'garfquerycronjobs')
def create_query_cj(
  body: kopf.Body,
  spec: kopf.Spec,
  name: str,
  namespace: str | None,
  logger: kopf.Logger,
  **kwargs,
) -> None:
  cronjob = _build_cron_job(
    name=name, namespace=namespace, spec=spec, cronjob_type=body['kind']
  )
  batch_v1 = kubernetes.client.BatchV1Api()
  try:
    batch_v1.create_namespaced_cron_job(namespace=namespace, body=cronjob)
    logger.info(f'Successfully created GarfQueryJob: {namespace}/{name}')
  except kubernetes.client.exceptions.ApiException as e:
    if e.status == 409:
      batch_v1.patch_namespaced_cron_job_status(
        name=name, namespace=namespace, body=cronjob
      )
      logger.info(f'GarfQueryJob exists, patching: {namespace}/{name}')
    else:
      raise kopf.PermanentError(f'Failed to create GarfQueryJob: {e}')


@kopf.on.delete('garf.io', 'v1', 'garfquerycronjobs')
def delete_query_cj(
  name: str, namespace: str | None, logger: kopf.Logger, **kwargs
) -> None:
  batch_v1 = kubernetes.client.BatchV1Api()
  try:
    batch_v1.delete_namespaced_cron_job(name=name, namespace=namespace)
    logger.info(f'Successfully deleted GarfQueryJob: {namespace}/{name}')
  except kubernetes.client.exceptions.ApiException as e:
    if e.status == 404:
      logger.info(f'GarfQueryJob {name} already deleted or does not exist')
    else:
      raise kopf.PermanentError(f'Failed to delete GarfQueryJob: {e}')
