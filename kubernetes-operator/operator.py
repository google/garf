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
  as_files: bool = True
  backoff_limit: int = 1
  active_deadline_seconds: int = 3600
  config_maps: dict[str, Any] = pydantic.Field(default_factory=dict)

  @property
  def command(self) -> list[str]:
    raise NotImplementedError

  @property
  def job_template(
    self,
  ) -> kubernetes.client.models.v1_job_template_spec.V1JobTemplateSpec:
    volumes = []
    volume_mounts = []
    if config := self.config_maps.get('config'):
      volume_mounts.append(
        {
          'name': 'config',
          'mountPath': '/app/config.yaml',
          'subPath': 'config.yaml',
        }
      )
      volumes.append(
        {
          'name': 'config',
          'configMap': {
            'name': config.get('name'),
            'items': [
              {
                'key': config.get('key'),
                'path': 'config.yaml',
              }
            ],
          },
        }
      )
    if workflow := self.config_maps.get('workflow'):
      volume_mounts.append(
        {
          'name': 'workflow',
          'mountPath': '/app/workflow.yaml',
          'subPath': 'workflow.yaml',
        }
      )
      volumes.append(
        {
          'name': 'workflow',
          'configMap': {
            'name': workflow.get('name'),
            'items': [
              {
                'key': workflow.get('key'),
                'path': 'workflow.yaml',
              }
            ],
          },
        }
      )
    return kubernetes.client.models.v1_job_template_spec.V1JobTemplateSpec(
      spec={
        'template': {
          'spec': {
            'volumes': volumes,
            'containers': [
              {
                'name': 'garf',
                'image': GARF_CLI_IMAGE,
                'args': self.command,
                'env': self.env,
                'volumeMounts': volume_mounts,
              }
            ],
            'restartPolicy': 'OnFailure',
          },
        },
        'backoffLimit': self.backoff_limit,
        'activeDeadlineSeconds': self.active_deadline_seconds,
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
      f' --source {self.source} --writer {self.writer}',
    ]
    if self.as_files:
      cli_args.append('--as-file')

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
    cli_args = ['workflow run', f'-f {self.workflow_path}']
    if self.as_files:
      cli_args.append('--as-file')

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


class RequiredFetcher(pydantic.BaseModel):
  name: str
  version: str | None = None

  def __str__(self) -> str:
    name = self.name if self.name.startswith('garf-') else f'garf-{self.name}'
    if not self.version:
      return name
    if self.version[0].isdigit():
      return f'{name}=={self.version}'
    return f'{name}{self.version}'


class Exporter(pydantic.BaseModel):
  source: str
  config_path: str
  delay_minutes: int = 15
  fetcher_parameters: dict[str, Any] = pydantic.Field(default_factory=dict)
  required_fetchers: list[RequiredFetcher] = pydantic.Field(
    default_factory=list
  )

  @property
  def init_command(self) -> list[str]:
    if not self.required_fetchers:
      return []
    return [
      '/venv/bin/pip',
      'install',
      '--no-cache-dir',
      '--target=/fetchers',
      *[str(fetcher) for fetcher in self.required_fetchers],
    ]

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
    config_path='/app/config.yaml'
    if spec.get('configMaps')
    else spec.get('configPath'),
    fetcher_parameters=spec.get('fetcherParameters') or {},
    required_fetchers=spec.get('requiredFetchers') or [],
  )
  if delay_minutes := spec.get('delayMinutes'):
    exporter.delay_minutes = int(delay_minutes)

  volume_mounts = []
  volumes = []
  init_containers = []
  env = list(spec.get('env') or [])
  env_from = []

  if config_maps := spec.get('configMaps'):
    volume_mounts.append(
      {
        'name': 'config',
        'mountPath': '/app/config.yaml',
        'subPath': 'config.yaml',
      }
    )
    volumes.append(
      {
        'name': 'config',
        'configMap': {
          'name': config_maps[0].get('name'),
          'items': [
            {
              'key': config_maps[0].get('key'),
              'path': 'config.yaml',
            }
          ],
        },
      }
    )

  for idx, secret in enumerate(spec.get('secrets') or []):
    secret_name = secret.get('name')
    secret_key = secret.get('key')
    secret_type = secret.get('type') or (
      'volume' if secret.get('mountPath') else 'env'
    )
    if secret_type == 'volume':
      vol_name = f'secret-{idx}-{secret_name}'
      mount_path = secret.get('mountPath') or f'/app/{secret_key}'
      volume_mount: dict[str, Any] = {
        'name': vol_name,
        'mountPath': mount_path,
        'subPath': os.path.basename(mount_path.rstrip('/')) or secret_key,
        'readOnly': True,
      }
      volume_mounts.append(volume_mount)
      volumes.append(
        {
          'name': vol_name,
          'secret': {
            'secretName': secret_name,
            'items': [
              {
                'key': secret_key,
                'path': secret_key,
              },
            ],
          },
        }
      )
    elif secret_key:
      env.append(
        {
          'name': secret.get('envName') or secret_key,
          'valueFrom': {
            'secretKeyRef': {
              'name': secret_name,
              'key': secret_key,
            }
          },
        }
      )
    else:
      env_from.append({'secretRef': {'name': secret_name}})

  if exporter.required_fetchers:
    volume_mounts.append(
      {
        'name': 'fetchers',
        'mountPath': '/fetchers',
      }
    )
    volumes.append(
      {
        'name': 'fetchers',
        'emptyDir': {},
      }
    )
    init_containers.append(
      {
        'name': 'install-fetchers',
        'image': GARF_EXPORTER_IMAGE,
        'command': exporter.init_command,
        'volumeMounts': [
          {
            'name': 'fetchers',
            'mountPath': '/fetchers',
          },
        ],
      }
    )
    env.append({'name': 'PYTHONPATH', 'value': '/app:/fetchers'})

  return kubernetes.client.V1Deployment(
    api_version='apps/v1',
    kind='Deployment',
    metadata={
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
          'annotations': {
            'prometheus.io/path': '/metrics',
            'prometheus.io/port': '8000',
            'prometheus.io/scrape': 'true',
          },
        },
        'spec': {
          'initContainers': init_containers,
          'containers': [
            {
              'name': 'garf-exporter',
              'image': GARF_EXPORTER_IMAGE,
              'args': exporter.command,
              'volumeMounts': volume_mounts,
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
              'env': env,
              'envFrom': env_from,
            }
          ],
          'volumes': volumes,
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
  common_job_parameters = {
    'config_path': '/app/config.yaml'
    if spec.get('configMaps', {}).get('config')
    else spec.get('configPath'),
    'enable_cache': bool(spec.get('enableCache', False)),
    'env': spec.get('env'),
    'backoff_limit': int(spec.get('backoffLimit', 1)),
    'active_deadline_seconds': int(spec.get('activeDeadlineSeconds', 3600)),
    'server_info': spec.get('server'),
    'config_maps': spec.get('configMaps') or {},
  }
  if job_type == 'Workflow':
    workflow_config_map = spec.get('configMaps', {}).get('workflow')
    if not spec.get('workflowPath') and not workflow_config_map:
      raise kopf.PermanentError(
        'Missing workflow definition. Either provide as workflowPath '
        'or as configMaps.workflow'
      )
    job = WorkflowJob(
      workflow_path='/app/workflow.yaml'
      if workflow_config_map
      else spec.get('workflowPath'),
      selected_aliases=spec.get('selectedAliases', []),
      skipped_aliases=spec.get('skippedAliases', []),
      as_files=bool(spec.get('workflowPath')),
      **common_job_parameters,
    )
  elif job_type == 'Query':
    job = GarfQueryJob(
      queries=spec.get('queries'),
      source=spec.get('source'),
      writer=spec.get('writer'),
      context=spec.get('context') or {},
      **common_job_parameters,
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
