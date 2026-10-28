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
GARF_EXPORTER_IMAGE: Final[str] = os.getenv(
  'GARF_EXPORTER_IMAGE', 'ghcr.io/google/garf-exporter:latest'
)


class ServerInfo(pydantic.BaseModel):
  url: str | None = None
  server_type: str = None

  def __bool__(self) -> bool:
    return bool(self.url and self.server_type)


class GarfJob(pydantic.BaseModel):
  context: dict[str, Any] = pydantic.Field(default_factory=dict)
  config_path: str | None = None
  server_info: ServerInfo | None = None
  enable_cache: bool = False
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
                'name': 'garf',
                'image': GARF_CLI_IMAGE,
                'args': self.command,
                'env': self.env,
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


class GarfQueryJob(GarfJob):
  queries: list[Query | QueryPath]
  source: str
  writer: str

  @property
  def command(self) -> list[str]:
    cli_args = [
      'execute',
      ' '.join(q.path for q in self.queries),
      f' --source {self.source} --writer {self.writer} --as-file',
    ]

    if server := self.server_info:
      cli_args.append(f'--endpoint={server.url}')

    if self.config_path:
      cli_args.append(f'--config {self.config_path}')
    if self.enable_cache:
      cli_args.append('--enable-cache')
    return ' '.join(cli_args).split()


class WorkflowJob(GarfJob):
  workflow_path: str
  selected_aliases: list[str] = pydantic.Field(default_factory=list)
  skipped_aliases: list[str] = pydantic.Field(default_factory=list)

  @property
  def command(self) -> list[str]:
    cli_args = ['workflow run', f'-f {self.workflow_path} --as-file']

    if server := self.server_info:
      cli_args.append(f'--endpoint={server.url}')

    if self.config_path:
      cli_args.append(f'--config {self.config_path}')
    if selected_aliases := ','.join(self.selected_aliases):
      cli_args.append(f'--selected-aliases {selected_aliases}')
    if skipped_aliases := ','.join(self.skipped_aliases):
      cli_args.append(f'--skipped-aliases {skipped_aliases}')
    if self.enable_cache:
      cli_args.append('--enable-cache')
    return ' '.join(cli_args).split()


class Exporter(pydantic.BaseModel):
  source: str
  config_path: str
  delay_minutes: int = 15
  fetcher_parameters: dict[str, Any] = pydantic.Field(default_factory=dict)

  @property
  def command(self):
    cli_args = [
      '/venv/bin/opentelemetry-instrument',
      '/venv/bin/python',
      '/app/garf/exporter/entrypoints/cli.py',
      '--source',
      self.source,
      '--config',
      self.config_path,
      '--delay-minutes',
      str(self.delay_minutes),
    ]
    for key, value in self.fetcher_parameters.items():
      cli_args.append(f'--source.{key}={value}')
    return ' '.join(cli_args).split()


def _create_exporter_deployment(
  name: str,
  namespace: str | None,
  spec: kopf.Spec,
  logger: kopf.Logger,
) -> kubernetes.client.V1Deployment:
  exporter = Exporter(
    source=spec.get('source'),
    config_path=spec.get('configPath'),
    fetcher_parameters=spec.get('fetcherParameters') or {},
  )
  if delay_minutes := spec.get('delayMinutes'):
    exporter.delay_minutes = int(delay_minutes)
  return kubernetes.client.V1Deployment(
    api_version='apps/v1',
    kind='Deployment',
    metadata={
      'annotations': {
        'prometheus.io/path': '/metrics',
        'prometheus.io/port': '8000',
        'prometheus.io/scrape': 'true',
      },
      'name': name,
      'namespace': namespace,
    },
    spec={
      'replicas': 1,
      'selector': {
        'matchLabels': {
          'app': name,
        },
      },
      'template': {
        'metadata': {
          'labels': {
            'app': name,
          },
        },
        'spec': {
          'containers': [
            {
              'name': 'garf-exporter',
              'image': GARF_EXPORTER_IMAGE,
              'args': exporter.command,
              'ports': [
                {
                  'containerPort': 8000,
                }
              ],
              'livenessProbe': {
                'httpGet': {'path': '/health', 'port': 8000},
                'initialDelaySeconds': 300,
                'periodSeconds': 20,
                'timeoutSeconds': 5,
                'failureThreshold': 3,
                'successThreshold': 1,
              },
              'env': spec.get('env'),
            }
          ],
        },
      },
    },
  )


def _build_job(
  name: str,
  namespace: str | None,
  spec: kopf.Spec,
  job_type: str,
  logger: kopf.Logger,
) -> kubernetes.client.V1CronJob:
  if job_type == 'Workflow':
    job = WorkflowJob(
      workflow_path=spec.get('workflowPath'),
      config_path=spec.get('configPath'),
      server_info=spec.get('server'),
      selected_aliases=spec.get('selectedAliases', []),
      skipped_aliases=spec.get('skippedAliases', []),
      enable_cache=bool(spec.get('enableCache', False)),
      env=spec.get('env'),
    )
  elif job_type == 'Query':
    job = GarfQueryJob(
      queries=spec.get('queries'),
      source=spec.get('source'),
      writer=spec.get('writer'),
      config_path=spec.get('configPath'),
      context=spec.get('context') or {},
      server_info=spec.get('server'),
      enable_cache=bool(spec.get('enableCache', False)),
      env=spec.get('env'),
    )
  else:
    raise kopf.PermanentError(f'Unknown job type: {job_type}')
  logger.info(
    'Creating %s: %s/%s with parameters: %s',
    job_type,
    namespace,
    name,
    ' '.join(job.command),
  )
  if schedule := spec.get('schedule'):
    return kubernetes.client.V1CronJob(
      api_version='batch/v1',
      kind='CronJob',
      metadata={
        'name': name,
        'namespace': namespace,
      },
      spec={
        'schedule': schedule,
        'jobTemplate': job.job_template,
      },
    )
  return kubernetes.client.V1Job(
    api_version='batch/v1',
    kind='Job',
    metadata={
      'name': name,
      'namespace': namespace,
    },
    spec=job.job_template.spec,
  )


@kopf.on.create('garf.io', 'v1', 'workflows')
def create_workflow(
  body: kopf.Body,
  spec: kopf.Spec,
  name: str,
  namespace: str | None,
  logger: kopf.Logger,
  **kwargs,
) -> None:
  job = _build_job(
    name=name,
    namespace=namespace,
    spec=spec,
    job_type=body['kind'],
    logger=logger,
  )
  batch_v1 = kubernetes.client.BatchV1Api()
  try:
    if spec.get('schedule'):
      batch_v1.create_namespaced_cron_job(namespace=namespace, body=job)
      logger.info(
        'Successfully created Workflow as CronJob: %s/%s', namespace, name
      )
    else:
      batch_v1.create_namespaced_job(namespace=namespace, body=job)
      logger.info(
        'Successfully created Workflow as Job: %s/%s', namespace, name
      )
  except kubernetes.client.exceptions.ApiException as e:
    if e.status == 409:
      if spec.get('schedule'):
        batch_v1.patch_namespaced_cron_job_status(
          name=name, namespace=namespace, body=job
        )
      else:
        batch_v1.patch_namespaced_job_status(
          name=name, namespace=namespace, body=job
        )
      logger.info('Workflow exists, patching: %s/%s', namespace, name)
    else:
      raise kopf.PermanentError(f'Failed to create Workflow: {e}')


@kopf.on.delete('garf.io', 'v1', 'workflows')
def delete_workflow(
  spec: kopf.Spec,
  name: str,
  namespace: str | None,
  logger: kopf.Logger,
  **kwargs,
) -> None:
  batch_v1 = kubernetes.client.BatchV1Api()
  try:
    if spec.get('schedule'):
      batch_v1.delete_namespaced_cron_job(name=name, namespace=namespace)
    else:
      batch_v1.delete_namespaced_job(name=name, namespace=namespace)
    logger.info('Successfully deleted Workflow: %s/%s', namespace, name)
  except kubernetes.client.exceptions.ApiException as e:
    if e.status == 404:
      logger.info('Workflow %s already deleted or does not exist', name)
    else:
      raise kopf.PermanentError(f'Failed to delete Workflow: {e}')


@kopf.on.create('garf.io', 'v1', 'queries')
def create_query(
  body: kopf.Body,
  spec: kopf.Spec,
  name: str,
  namespace: str | None,
  logger: kopf.Logger,
  **kwargs,
) -> None:
  job = _build_job(
    name=name,
    namespace=namespace,
    spec=spec,
    job_type=body['kind'],
    logger=logger,
  )
  batch_v1 = kubernetes.client.BatchV1Api()
  try:
    if spec.get('schedule'):
      batch_v1.create_namespaced_cron_job(namespace=namespace, body=job)
      logger.info(
        'Successfully created Query as CronJob: %s/%s', namespace, name
      )
    else:
      batch_v1.create_namespaced_job(namespace=namespace, body=job)
      logger.info('Successfully created Query as Job: %s/%s', namespace, name)
  except kubernetes.client.exceptions.ApiException as e:
    if e.status == 409:
      batch_v1.patch_namespaced_cron_job_status(
        name=name, namespace=namespace, body=job
      )
      logger.info(f'Query exists, patching: {namespace}/{name}')
    else:
      raise kopf.PermanentError(f'Failed to create Query: {e}')


@kopf.on.delete('garf.io', 'v1', 'queries')
def delete_query(
  spec: kopf.Spec,
  name: str,
  namespace: str | None,
  logger: kopf.Logger,
  **kwargs,
) -> None:
  batch_v1 = kubernetes.client.BatchV1Api()
  try:
    if spec.get('schedule'):
      batch_v1.delete_namespaced_cron_job(name=name, namespace=namespace)
    else:
      batch_v1.delete_namespaced_job(name=name, namespace=namespace)
    logger.info('Successfully deleted GarfQueryJob: %s/%s', namespace, name)
  except kubernetes.client.exceptions.ApiException as e:
    if e.status == 404:
      logger.info('GarfQueryJob %s already deleted or does not exist', name)
    else:
      raise kopf.PermanentError(f'Failed to delete Query: {e}')


@kopf.on.create('garf.io', 'v1', 'exporters')
def create_exporter(
  body: kopf.Body,
  spec: kopf.Spec,
  name: str,
  namespace: str | None,
  logger: kopf.Logger,
  **kwargs,
) -> None:
  deployment = _create_exporter_deployment(
    name=name,
    namespace=namespace,
    spec=spec,
    logger=logger,
  )
  apps = kubernetes.client.AppsV1Api()
  try:
    apps.create_namespaced_deployment(namespace=namespace, body=deployment)
    logger.info(
      'Successfully created Exporter Deployment: %s/%s', namespace, name
    )
  except kubernetes.client.exceptions.ApiException as e:
    if e.status == 409:
      apps.patch_namespaced_deployment(
        name=name, namespace=namespace, body=deployment
      )
      logger.info('Exporter exists, patching: %s/%s', namespace, name)
    else:
      raise kopf.PermanentError(f'Failed to create Exporter: {e}')


@kopf.on.delete('garf.io', 'v1', 'exporters')
def delete_exporter(
  spec: kopf.Spec,
  name: str,
  namespace: str | None,
  logger: kopf.Logger,
  **kwargs,
) -> None:
  apps = kubernetes.client.AppsV1Api()
  try:
    apps.delete_namespaced_deployment(name=name, namespace=namespace)
    logger.info(
      'Successfully deleted Exporter Deployment: %s/%s', namespace, name
    )
  except kubernetes.client.exceptions.ApiException as e:
    if e.status == 404:
      logger.info('Exporter %s already deleted or does not exist', name)
    else:
      raise kopf.PermanentError(f'Failed to delete Exporter: {e}')
